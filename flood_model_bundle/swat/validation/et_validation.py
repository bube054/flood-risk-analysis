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

Run:  python et_validation.py
"""

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


def main():
    ref = basin_mean_et()
    sim = load_swat_et()

    keys = sorted(k for k in sim if k in ref)
    obs_v = [ref[k] for k in keys]
    sim_v = [sim[k] for k in keys]

    # monthly climatology (12 values) - the seasonal-cycle test
    clim_o, clim_s = [], []
    for m in range(1, 13):
        oo = [ref[k] for k in keys if k[1] == m]
        ss = [sim[k] for k in keys if k[1] == m]
        clim_o.append(sum(oo) / len(oo))
        clim_s.append(sum(ss) / len(ss))

    res = {
        "reference_product": "TerraClimate aet v1 (Abatzoglou et al. 2018), ~4km monthly",
        "reference_is_not_mod16": True,
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

    (HERE / "et_validation_results.json").write_text(json.dumps(res, indent=2))

    with open(HERE / "et_monthly_comparison.csv", "w", newline="\n") as f:
        f.write("month,terraclimate_aet_mm,swat_et_mm\n")
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
    print("  ref:", " ".join(f"{v:5.1f}" for v in c["ref_mm"]))
    print("  sim:", " ".join(f"{v:5.1f}" for v in c["sim_mm"]))


if __name__ == "__main__":
    main()
