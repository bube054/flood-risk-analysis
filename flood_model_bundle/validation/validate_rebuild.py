# -*- coding: utf-8 -*-
"""Validate a hand-rebuilt susceptibility map against the published one.

Runs the thesis's Test A (Section 3.8.2) — MODIS 250 m observed flood extent for
Lagos, Jul–Nov 2012 — twice: once on models/core (the published map) and once on a
rebuild produced in QGIS. Prints them side by side.

Usage
-----
    python validate_rebuild.py [REBUILD_DIR]

REBUILD_DIR must contain FSI.tif and hazard_zones.tif.
Defaults to C:\\Users\\bube\\Desktop\\aligned.
"""
import sys
from pathlib import Path

import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spatial_validation as SV          # reuse auc_roc / confusion_at_youden

CORE = HERE.parent / "models" / "core"
DEFAULT_REBUILD = Path(r"C:\Users\bube\Desktop\aligned")
ZONE_NAMES = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}


def test_a(index_path, zones_path, lagos, flood_geom):
    """Test A for one (index, zones) pair. Mirrors spatial_validation.test_a()."""
    with rasterio.open(index_path) as si, rasterio.open(zones_path) as sz:
        idx_f, _ = rasterio.mask.mask(si, [flood_geom], crop=True, filled=True)
        zon_f, _ = rasterio.mask.mask(sz, [flood_geom], crop=True, filled=True)
        idx_l, _ = rasterio.mask.mask(si, [lagos], crop=True, filled=True)
        zon_l, _ = rasterio.mask.mask(sz, [lagos], crop=True, filled=True)

    fi, fz, li, lz = idx_f[0], zon_f[0], idx_l[0], zon_l[0]
    m_f = (fi != -9999) & np.isfinite(fi) & (fz > 0)
    m_l = (li != -9999) & np.isfinite(li) & (lz > 0)
    flood_vals, flood_zones = fi[m_f], fz[m_f]
    lagos_vals, lagos_zones = li[m_l], lz[m_l]

    # pseudo-absence sample, same seed as the thesis script so runs are comparable
    n_abs = min(len(flood_vals) * 5, len(lagos_vals))
    absence = np.random.default_rng(42).choice(lagos_vals, size=n_abs, replace=False)

    auc = SV.auc_roc(flood_vals.tolist(), absence.tolist())
    cm = SV.confusion_at_youden(flood_vals.tolist(), absence.tolist())

    enrich = {}
    for z in range(1, 6):
        f_share = float((flood_zones == z).sum()) / len(flood_zones) * 100
        l_share = float((lagos_zones == z).sum()) / len(lagos_zones) * 100
        enrich[ZONE_NAMES[z]] = (round(f_share, 2), round(l_share, 2),
                                 round(f_share / l_share, 2) if l_share > 0 else 0.0)

    hi_f = sum(enrich[z][0] for z in ("High", "Very High"))
    hi_l = sum(enrich[z][1] for z in ("High", "Very High"))
    return {
        "flood_cells": len(flood_vals),
        "lagos_cells": len(lagos_vals),
        "auc": auc,
        "cm": cm,
        "enrich": enrich,
        "hi_f": hi_f,
        "hi_l": hi_l,
        "hi_enr": round(hi_f / hi_l, 2) if hi_l else 0.0,
        "mean_f": float(flood_vals.mean()),
        "mean_l": float(lagos_vals.mean()),
    }


def main():
    rebuild = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REBUILD
    r_idx, r_zon = rebuild / "FSI.tif", rebuild / "hazard_zones.tif"
    missing = [p for p in (r_idx, r_zon) if not p.exists()]
    if missing:
        print("Cannot find your rebuild. Missing:")
        for p in missing:
            print("   ", p)
        print("\nPass the folder explicitly:  python validate_rebuild.py <folder>")
        return 1

    print("Loading Lagos boundary and the observed 2012 flood extent ...")
    lgas = gpd.read_file(CORE / "lagos_lgas.geojson").to_crs("EPSG:32631")
    lagos = lgas.union_all() if hasattr(lgas, "union_all") else lgas.unary_union
    flood = gpd.read_file(SV.FLOOD_2012).to_crs("EPSG:32631")
    flood = flood.clip(gpd.GeoSeries([lagos], crs="EPSG:32631"))
    if flood.empty:
        print("No 2012 flood polygons inside Lagos - aborting.")
        return 1
    fgeom = flood.union_all() if hasattr(flood, "union_all") else flood.unary_union

    print("Running Test A on the PUBLISHED map ...")
    pub = test_a(CORE / "flood_hazard_index.tif", CORE / "flood_hazard_zones.tif", lagos, fgeom)
    print("Running Test A on YOUR REBUILD  ...")
    mine = test_a(r_idx, r_zon, lagos, fgeom)

    bar = "=" * 68
    print("\n" + bar)
    print("TEST A  -  vs MODIS 250 m observed flood extent, Lagos, Jul-Nov 2012")
    print(bar)
    print("%-34s %14s %14s" % ("", "PUBLISHED", "YOUR REBUILD"))
    rows = [
        ("observed flood cells", "%14d", pub["flood_cells"], mine["flood_cells"]),
        ("observed flood area (km2)", "%14.1f",
         pub["flood_cells"] * 900 / 1e6, mine["flood_cells"] * 900 / 1e6),
        ("Lagos cells", "%14d", pub["lagos_cells"], mine["lagos_cells"]),
        ("AUC-ROC   (0.5 = no skill)", "%14.3f", pub["auc"], mine["auc"]),
        ("sensitivity at Youden", "%14.3f", pub["cm"]["sensitivity"], mine["cm"]["sensitivity"]),
        ("specificity at Youden", "%14.3f", pub["cm"]["specificity"], mine["cm"]["specificity"]),
        ("mean index, flooded cells", "%14.4f", pub["mean_f"], mine["mean_f"]),
        ("mean index, all Lagos", "%14.4f", pub["mean_l"], mine["mean_l"]),
    ]
    for label, fmt, a, b in rows:
        print(("%-34s " + fmt + " " + fmt) % (label, a, b))

    print("\nENRICHMENT  (share of observed flood / share of Lagos area)")
    print("%-14s %12s %12s   %12s %12s"
          % ("zone", "published", "yours", "pub % flood", "your % flood"))
    for z in ("Very Low", "Low", "Moderate", "High", "Very High"):
        print("%-14s %12.2f %12.2f   %11.2f%% %11.2f%%"
              % (z, pub["enrich"][z][2], mine["enrich"][z][2],
                 pub["enrich"][z][0], mine["enrich"][z][0]))
    print("%-14s %12.2f %12.2f   %11.2f%% %11.2f%%"
          % ("High+V.High", pub["hi_enr"], mine["hi_enr"], pub["hi_f"], mine["hi_f"]))

    mono = [mine["enrich"][z][2] for z in ("Low", "Moderate", "High", "Very High")]
    rises = all(mono[i] <= mono[i + 1] for i in range(len(mono) - 1))
    d_auc = abs(pub["auc"] - mine["auc"])

    print("\n" + bar)
    print("VERDICT")
    print(bar)
    print("  AUC difference vs published      : %.4f  %s"
          % (d_auc, "(agrees)" if d_auc < 0.01 else "(DIVERGES - investigate)"))
    print("  enrichment rises Low -> V.High   : %s   %s"
          % ("YES" if rises else "NO", mono))
    print("  thesis target AUC 0.70           : %s for BOTH maps"
          % ("met" if mine["auc"] >= 0.70 else "NOT met"))
    print("\n  A rebuild that reproduces the published AUC to within 0.01 and keeps")
    print("  monotonic enrichment is reproducing the model, not just the picture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
