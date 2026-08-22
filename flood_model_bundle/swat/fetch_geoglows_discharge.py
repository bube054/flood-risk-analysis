"""
fetch_geoglows_discharge.py — pull modelled daily streamflow for the Ogun River
================================================================================
GEOGLOWS (ECMWF) global streamflow model: daily simulated discharge 1979-present
for any river reach, free, no login. This is the calibration/validation target
for the SWAT+ model (data-scarce route; see SWAT_BUILD_PLAN.md §1).

Run (needs Python 3.9 — geoglows depends on numba/llvmlite):
    uv run --python 3.9 --with geoglows --with pandas python fetch_geoglows_discharge.py
"""
import sys
import geoglows
import pandas as pd

# Point on the lower Ogun River main stem (near Kara/Akute, above the lagoon).
# Adjust once you delineate the catchment and know the exact SWAT outlet.
LAT, LON = 6.65, 3.38
OUT = "geoglows_ogun_discharge.csv"


def find_river_id(lat, lon):
    for fn in ("latlon_to_river", "latlon_to_reach", "latlon_to_riverid"):
        f = getattr(geoglows.streams, fn, None)
        if f:
            try:
                return f(lat, lon), fn
            except Exception as e:                       # noqa: BLE001
                print(f"  {fn} failed: {e}")
    raise SystemExit("Could not resolve a river id from lat/lon — check geoglows API")


def get_retrospective(river_id):
    for fn in ("retrospective", "historical_simulation", "retrospective_daily"):
        f = getattr(geoglows.data, fn, None)
        if f:
            try:
                return f(river_id), fn
            except Exception as e:                       # noqa: BLE001
                print(f"  {fn} failed: {e}")
    raise SystemExit("Could not pull retrospective data — check geoglows API")


if __name__ == "__main__":
    print("geoglows", getattr(geoglows, "__version__", "?"))
    rid, how = find_river_id(LAT, LON)
    print(f"Ogun reach near ({LAT},{LON}) -> river_id={rid} (via {how})")
    df, how2 = get_retrospective(rid)
    print(f"Retrieved {len(df)} rows via {how2}; columns={list(df.columns)[:3]}")
    df.to_csv(OUT)
    # monthly means — the timestep your thesis evaluates at
    try:
        monthly = df.resample("MS").mean()
        monthly.to_csv("geoglows_ogun_discharge_monthly.csv")
        print("Saved daily ->", OUT, "and monthly means")
    except Exception as e:                               # noqa: BLE001
        print("Saved daily ->", OUT, "(monthly resample skipped:", e, ")")
    print(df.tail(3).to_string())
