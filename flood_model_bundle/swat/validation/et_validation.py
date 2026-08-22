"""
Independent ET validation of the calibrated Ogun SWAT+ model.
================================================================

WHY THIS EXISTS
---------------
The SWAT+ model was calibrated against GEOGLOWS modelled discharge (see
METHODOLOGY_LOG.md sec.9). That leaves one weakness: calibration and validation
both used the SAME data source, split only by time period. Nothing outside
GEOGLOWS ever checked the model.

This script adds a genuinely INDEPENDENT check, using a second, unrelated
variable (evapotranspiration) from a second, unrelated data source. This is the
multi-variable data-scarce strategy of Odusanya et al. (2019).

Crucially, the model was NEVER tuned to ET. Every parameter was fitted to
discharge alone. So agreement here is an independent test, not a fitted result.

DATA SOURCE - READ THIS BEFORE CITING
-------------------------------------
Reference ET = TerraClimate `aet` (Abatzoglou et al. 2018), ~4 km monthly.
This is NOT MODIS MOD16. MOD16 was the original intent, but it is only
reachable through Google Earth Engine or NASA Earthdata, both of which need an
interactive login this script cannot perform. The ORNL DAAC MODIS REST API
(the no-login route) was down (HTTP 500 on all endpoints) when this was run.

TerraClimate is a climatic water-balance product, not a direct satellite
retrieval. That makes it a weaker independence claim than MOD16 would be --
state this plainly. `fetch_mod16_et_gee.js` in this folder reproduces the same
analysis with true MODIS ET once you can log in to GEE.

Run:  python et_validation.py                                  # TerraClimate (bundled)
      python et_validation.py --reference mod16_et_ogun_monthly.csv   # true MODIS ET
"""

import argparse
import calendar
import csv
import json
import math
from pathlib import Path

import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd

HERE = Path(__file__).resolve().parent
# Source netCDFs are vendored into the repo so this is reproducible offline.
NC_DIR = HERE.parent.parent / "validation" / "data" / "terraclimate"
WSHED = Path(r"C:\SWAT_Ogun\OgunModel2\Watershed\Shapes\ogun_dem_90m_clipwshed.shp")
SWAT_ET = HERE / "swat_et_monthly.csv"

YEARS = range(2011, 2024)
SCALE = 0.1  # TerraClimate aet scale_factor; NCSS returns raw Int16


# ── statistics (same definitions as calib.py, Moriasi et al. 2007) ──────────
def nse(obs, sim):
    mo = sum(obs) / len(obs)
    return 1 - sum((o - s) ** 2 for o, s in zip(obs, sim)) / sum((o - mo) ** 2 for o in obs)


def pbias(obs, sim):
    return 100 * sum(o - s for o, s in zip(obs, sim)) / sum(obs)


def r2(obs, sim):
    mo, ms = sum(obs) / len(obs), sum(sim) / len(sim)
    soo = sum((o - mo) ** 2 for o in obs)
    sss = sum((s - ms) ** 2 for s in sim)
    sos = sum((o - mo) * (s - ms) for o, s in zip(obs, sim))
    return (sos / math.sqrt(soo * sss)) ** 2 if soo * sss > 0 else 0.0


def rmse(obs, sim):
    return math.sqrt(sum((o - s) ** 2 for o, s in zip(obs, sim)) / len(obs))


# ── basin-mean reference ET ────────────────────────────────────────────────
def basin_mean_et():
    """Monthly basin-mean TerraClimate AET, masked to the SWAT watershed."""
    basin = gpd.read_file(WSHED).to_crs("EPSG:4326")
    geom = [basin.union_all() if hasattr(basin, "union_all") else basin.unary_union]

    out = {}
    for y in YEARS:
        path = NC_DIR / f"aet_{y}.nc"
        with rasterio.open(f"netcdf:{path}:aet") as src:
            # NCSS subset carries no CRS; TerraClimate is plain WGS84.
            data, _ = rasterio.mask.mask(
                _with_crs(src), geom, crop=True, nodata=-32768, indexes=list(range(1, 13))
            )
        for m in range(12):
            band = data[m].astype("float64")
            valid = band[(band != -32768) & np.isfinite(band)]
            out[(y, m + 1)] = float(valid.mean()) * SCALE
    return out


class _with_crs:
    """Wrap a CRS-less netCDF dataset so rasterio.mask accepts it."""

    def __init__(self, src):
        self._src = src

    def __getattr__(self, k):
        return getattr(self._src, k)

    @property
    def crs(self):
        return rasterio.crs.CRS.from_epsg(4326)


def load_swat_et():
    rows = SWAT_ET.read_text().strip().splitlines()[1:]
    out = {}
    for r in rows:
        mon, et, pcp, pet = r.split(",")
        y, m = mon.split("-")
        out[(int(y), int(m))] = float(et)
    return out


def load_mod16_csv(path):
    """Read a MOD16 CSV produced by fetch_mod16_et_gee.js.

    Expected columns: `month` (YYYY-MM) and `mod16_et_mm` (mm/month, already
    scaled by the GEE script). Rows with a blank value are skipped -- GEE emits
    empty cells where a month had no valid composites.
    """
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            val = (row.get("mod16_et_mm") or "").strip()
            if not val:
                continue
            y, m = row["month"].split("-")
            out[(int(y), int(m))] = float(val)
    if not out:
        raise SystemExit(f"No usable rows in {path} (expected month, mod16_et_mm).")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--reference",
        metavar="CSV",
        help="MOD16 CSV from fetch_mod16_et_gee.js. Omit to use the bundled "
             "TerraClimate netCDFs.",
    )
    args = ap.parse_args()

    if args.reference:
        ref = load_mod16_csv(args.reference)
        ref_name = f"MODIS MOD16A2GF (satellite ET) - {Path(args.reference).name}"
        is_mod16 = True
    else:
        ref = basin_mean_et()
        ref_name = "TerraClimate aet v1 (Abatzoglou et al. 2018), ~4km monthly"
        is_mod16 = False

    sim = load_swat_et()

    keys = sorted(k for k in sim if k in ref)
    obs_v = [ref[k] for k in keys]
    sim_v = [sim[k] for k in keys]

    # Monthly climatology (12 values) - the seasonal-cycle test.
    # A calendar month can be empty if the reference has gaps (GEE emits blank
    # cells for months with no valid composites), so skip those rather than
    # dividing by zero. months_covered records what actually contributed.
    clim_o, clim_s, months_covered = [], [], []
    for m in range(1, 13):
        oo = [ref[k] for k in keys if k[1] == m]
        ss = [sim[k] for k in keys if k[1] == m]
        if not oo:
            continue
        months_covered.append(m)
        clim_o.append(sum(oo) / len(oo))
        clim_s.append(sum(ss) / len(ss))
    if len(clim_o) < 12:
        print(f"WARNING: reference covers only {len(clim_o)}/12 calendar months "
              f"{months_covered} - climatology statistics are partial.")

    res = {
        "reference_product": ref_name,
        "reference_is_not_mod16": not is_mod16,
        "independence_note": (
            "SWAT+ was calibrated on GEOGLOWS discharge only; no ET term entered "
            "the objective function. This is an independent multi-variable test."
        ),
        "n_months": len(keys),
        "period": f"{keys[0][0]}-{keys[0][1]:02d} to {keys[-1][0]}-{keys[-1][1]:02d}",
        "monthly": {
            "nse": round(nse(obs_v, sim_v), 3),
            "r2": round(r2(obs_v, sim_v), 3),
            "pbias": round(pbias(obs_v, sim_v), 2),
            "rmse_mm": round(rmse(obs_v, sim_v), 2),
            "mean_ref_mm": round(sum(obs_v) / len(obs_v), 1),
            "mean_sim_mm": round(sum(sim_v) / len(sim_v), 1),
        },
        "months_covered": months_covered,
        "climatology": {
            "nse": round(nse(clim_o, clim_s), 3),
            "r2": round(r2(clim_o, clim_s), 3),
            "pbias": round(pbias(clim_o, clim_s), 2),
            "ref_mm": [round(v, 1) for v in clim_o],
            "sim_mm": [round(v, 1) for v in clim_s],
        },
        "annual_mm": {
            "reference": round(sum(obs_v) / (len(obs_v) / 12), 0),
            "swat": round(sum(sim_v) / (len(sim_v) / 12), 0),
        },
    }

    # MOD16 runs write to their own files so a TerraClimate baseline is never
    # silently overwritten -- keep both so the two references can be compared.
    tag = "_mod16" if is_mod16 else ""
    col = "mod16_et_mm" if is_mod16 else "terraclimate_aet_mm"

    (HERE / f"et_validation_results{tag}.json").write_text(json.dumps(res, indent=2))

    with open(HERE / f"et_monthly_comparison{tag}.csv", "w", newline="\n") as f:
        f.write(f"month,{col},swat_et_mm\n")
        for k in keys:
            f.write(f"{k[0]}-{k[1]:02d},{ref[k]:.2f},{sim[k]:.2f}\n")

    m = res["monthly"]
    c = res["climatology"]
    print(f"Reference : {res['reference_product']}")
    print(f"Months    : {res['n_months']}  ({res['period']})")
    print(f"Annual ET : reference {res['annual_mm']['reference']:.0f} mm/yr  "
          f"vs SWAT {res['annual_mm']['swat']:.0f} mm/yr")
    print(f"Monthly   : NSE {m['nse']:+.2f}  R2 {m['r2']:.2f}  "
          f"PBIAS {m['pbias']:+.1f}%  RMSE {m['rmse_mm']:.1f} mm")
    print(f"Climatology: NSE {c['nse']:+.2f}  R2 {c['r2']:.2f}  PBIAS {c['pbias']:+.1f}%")
    print("\nmonthly climatology (mm):")
    print("  mon:", " ".join(f"{calendar.month_abbr[m]:>5}" for m in res["months_covered"]))
    print("  ref:", " ".join(f"{v:5.1f}" for v in c["ref_mm"]))
    print("  sim:", " ".join(f"{v:5.1f}" for v in c["sim_mm"]))


if __name__ == "__main__":
    main()
