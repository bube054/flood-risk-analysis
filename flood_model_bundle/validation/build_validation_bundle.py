"""
Merge every validation result into one file the portal can serve.

Writes models/core/validation_results.json, consuming:
  - swat/validation/et_validation_results.json      (independent ET check)
  - validation/spatial_validation_results.json      (hazard map vs observed floods)
  - the discharge/ET trade-off measured by calib_joint.py (recorded below)

Run:  python build_validation_bundle.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
CORE = BUNDLE / "models" / "core"

# Measured by calib_joint.py. Each row is one full SWAT+ run scored against
# BOTH GEOGLOWS discharge and TerraClimate ET. petco's allowed ceiling is 1.20;
# reaching 1.35/1.50 required temporarily raising it in cal_parms.cal (restored
# afterwards), so those rows are diagnostic, not deliverable parameter sets.
TRADEOFF = {
    "description": (
        "Multi-variable calibration probe. Raising petco improves ET "
        "monotonically while degrading discharge. Only the incumbent meets all "
        "three thesis discharge thresholds, so the incumbent is retained."
    ),
    "thresholds": {"nse": 0.50, "r2": 0.60, "abs_pbias": 25},
    "runs": [
        {"petco": 1.20, "incumbent": True,
         "discharge": {"nse": 0.507, "r2": 0.606, "pbias": 1.6},
         "et": {"nse": 0.180, "r2": 0.394, "pbias": 12.5},
         "discharge_passes": True},
        {"petco": 1.35, "incumbent": False,
         "discharge": {"nse": 0.530, "r2": 0.596, "pbias": 15.7},
         "et": {"nse": 0.303, "r2": 0.386, "pbias": 6.6},
         "discharge_passes": False,
         "fails_on": "R2 0.596 < 0.60"},
        {"petco": 1.50, "incumbent": False,
         "discharge": {"nse": 0.507, "r2": 0.583, "pbias": 28.7},
         "et": {"nse": 0.367, "r2": 0.386, "pbias": 1.1},
         "discharge_passes": False,
         "fails_on": "R2 0.583 < 0.60 and PBIAS 28.7% > 25%"},
    ],
    "diagnosis": (
        "petco (PET multiplier) is pinned at its allowed maximum of 1.20 in the "
        "calibrated set. Independently, TerraClimate indicates SWAT+ ET is ~12.5% "
        "too low. Two separate lines of evidence therefore agree that the model "
        "wants more evapotranspiration than the parameter range permits."
    ),
}


def main():
    svd = BUNDLE / "swat" / "validation"
    sp = json.loads((HERE / "spatial_validation_results.json").read_text())

    # MOD16 (true satellite ET) is the primary reference -- this is the product
    # the supervisor asked for. TerraClimate is retained as a second, unrelated
    # reference: the two agreeing matters more than either alone.
    mod16_path = svd / "et_validation_results_mod16.json"
    tc_path = svd / "et_validation_results.json"
    if mod16_path.exists():
        et = json.loads(mod16_path.read_text())
        et_alt = json.loads(tc_path.read_text()) if tc_path.exists() else None
    else:
        et = json.loads(tc_path.read_text())
        et_alt = None

    out = {
        "summary": (
            "Two independent validations added after the discharge calibration: "
            "(1) an ET check the model was never tuned to, and (2) a spatial "
            "check of the AHP hazard map against observed floods. Neither is a "
            "pass/fail certificate -- read the caveats on each."
        ),
        "et_validation": et,
        "et_validation_corroborating": et_alt,
        "et_two_reference_note": (
            "Two unrelated ET products were tested: MODIS MOD16A2GF (satellite "
            "retrieval, primary) and TerraClimate (climatic water balance). They "
            "agree with each other -- 920 vs 900 mm/yr, and both show the same "
            "damped seasonal cycle in SWAT+. Agreement between two independent "
            "references makes the finding robust rather than an artefact of one "
            "product."
        ) if et_alt else None,
        "et_aoi_correction_note": (
            "MOD16 was first exported over a bounding box (40,397 km2) rather than "
            "the delineated basin (19,915 km2), so about half the sampled pixels lay "
            "outside the catchment. Re-exported over the true basin outline, the "
            "annual mean moved only 935 -> 920 mm/yr and monthly NSE 0.09 -> 0.14. "
            "The correction was methodologically necessary but changed no conclusion "
            "-- which is itself evidence the ET finding is not an artefact of how the "
            "sampling region was drawn."
        ),
        "spatial_validation": sp,
        "multivariable_calibration_tradeoff": TRADEOFF,
        "honest_status": {
            "et_independent_check": "PARTIAL - against MODIS MOD16 sampled over the true "
                                    "basin, volume is within 14.4% (inside the +/-25% "
                                    "Moriasi band) but seasonal dynamics are weak (monthly "
                                    "NSE 0.14). SWAT+ swings ~26 mm across the year against "
                                    "MODIS's ~86 mm, so the seasonal amplitude is roughly 3x "
                                    "too flat. TerraClimate independently shows the same "
                                    "pattern.",
            "hazard_map_pixel_level": "MODEST SKILL - AUC-ROC 0.62 against the 2012 "
                                      "MODIS flood extent; zone enrichment rises "
                                      "monotonically to 1.61x in Very High.",
            "hazard_map_lga_level": "INCONCLUSIVE - NEMA report counts track raw "
                                    "population (rho 0.57) far better than modelled "
                                    "exposure (rho 0.17), so the test is confounded "
                                    "by reporting effort and cannot validate the map.",
            "not_claimed": "None of this establishes forecast skill. The map remains "
                           "an AHP susceptibility index, now with a measured and "
                           "modest correspondence to one observed flood event.",
        },
    }
    p = CORE / "validation_results.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
