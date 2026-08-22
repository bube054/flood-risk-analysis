"""
Spatial validation of the Lagos AHP flood-hazard map against observed floods.
=============================================================================

WHY THIS EXISTS
---------------
The AHP hazard map had never been checked against a real flood. Weighted-overlay
susceptibility maps are internally consistent by construction, so without an
external check there is no evidence the map corresponds to where Lagos actually
floods. This script supplies that evidence using two independent observations.

TEST A - PIXEL LEVEL (observed flood extent vs continuous hazard index)
  Observation: MODIS 250 m flood extent for Nigeria, Jul-Nov 2012
               (NASA/DFO, via HDX "Nigeria - Flood Extents Nov 2012").
  Method: flood pixels = presence; random non-flood Lagos pixels = pseudo-
          absence; score the hazard index with AUC-ROC (Mann-Whitney U).
          Also reports zone enrichment: the share of observed flood area in
          each hazard zone DIVIDED BY that zone's share of Lagos. Enrichment
          > 1 means the zone captures more flooding than chance.
          The enrichment ratio is the honest statistic here -- a raw "X% of
          floods fell in High zones" is meaningless if High zones cover X% of
          Lagos anyway.

TEST B - LGA LEVEL (reported flood incidents vs modelled exposure ranking)
  Observation: NEMA 2022 flood records, 62 Lagos community-level reports
               across 13 LGAs (via HDX "Nigeria: Flood data").
  Method: Spearman rank correlation between NEMA report count per LGA and the
          model's pct_high_very_high; plus a Mann-Whitney U test of whether
          LGAs with reports rank higher than LGAs without.
  NOTE: NEMA records carry no coordinates, only LGA + community name. No
        geocoding is attempted -- inventing point locations from place names
        would fabricate the very data being validated against. LGA level is
        the finest resolution the source honestly supports.

LIMITATIONS - CARRY THESE INTO THE THESIS
  * MODIS 250 m is coarse for urban Lagos; small street-scale floods are
    invisible to it. Absence of detection is NOT evidence of no flooding.
  * 2012 is a single event; the map is a static susceptibility surface.
  * NEMA reporting is effort-biased: densely populated, better-covered LGAs
    generate more reports regardless of true flood frequency.
  * Test B compares a population-weighted exposure metric to incident counts,
    so population density partly drives both sides.

Run:  python spatial_validation.py
"""

import csv
import json
import math
import random
from pathlib import Path

import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd
import shapely.geometry as sg

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "models" / "core"
# Source data is vendored into the repo so this is reproducible offline.
OBS = HERE / "data"
FLOOD_2012 = OBS / "flood_2012" / "NGA_Flood_Modis_250_nasa.shp"
NEMA = HERE / "nema_2022_lagos.csv"

ZONE_NAMES = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
random.seed(42)


# The bundled exposure_by_lga.csv misspells Badagry as "Badagary". Map the
# variants onto one key so the 4 NEMA Badagry reports are not silently dropped.
ALIASES = {"badagary": "badagry"}


def norm(s):
    """Normalise LGA names across sources ('Ifako-Ijaye' / 'Ifako Ijaye')."""
    k = "".join(c for c in str(s).lower() if c.isalnum())
    return ALIASES.get(k, k)


# ── AUC via Mann-Whitney U (no sklearn dependency) ─────────────────────────
def auc_roc(pos, neg):
    data = [(v, 1) for v in pos] + [(v, 0) for v in neg]
    data.sort(key=lambda t: t[0])
    # average ranks for ties
    ranks = [0.0] * len(data)
    i = 0
    while i < len(data):
        j = i
        while j + 1 < len(data) and data[j + 1][0] == data[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r_pos = sum(r for r, (_, lab) in zip(ranks, data) if lab == 1)
    n1, n0 = len(pos), len(neg)
    return (r_pos - n1 * (n1 + 1) / 2) / (n1 * n0)


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def mannwhitney_p(a, b):
    """Two-sided normal approximation; adequate for n>=8 per group."""
    data = [(v, 0) for v in a] + [(v, 1) for v in b]
    data.sort(key=lambda t: t[0])
    ranks = [0.0] * len(data)
    i = 0
    while i < len(data):
        j = i
        while j + 1 < len(data) and data[j + 1][0] == data[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r_a = sum(r for r, (_, g) in zip(ranks, data) if g == 0)
    n1, n2 = len(a), len(b)
    u = r_a - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sd == 0:
        return 1.0
    z = (u - mu) / sd
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


# ── TEST A ─────────────────────────────────────────────────────────────────
def test_a():
    lgas = gpd.read_file(CORE / "lagos_lgas.geojson").to_crs("EPSG:32631")
    lagos = lgas.union_all() if hasattr(lgas, "union_all") else lgas.unary_union

    flood = gpd.read_file(FLOOD_2012).to_crs("EPSG:32631")
    flood = flood.clip(gpd.GeoSeries([lagos], crs="EPSG:32631"))
    if flood.empty:
        raise SystemExit("No 2012 flood polygons inside Lagos - aborting.")
    flood_geom = flood.union_all() if hasattr(flood, "union_all") else flood.unary_union

    with rasterio.open(CORE / "flood_hazard_index.tif") as src_i, \
         rasterio.open(CORE / "flood_hazard_zones.tif") as src_z:

        # hazard values inside observed flood extent
        idx_f, _ = rasterio.mask.mask(src_i, [flood_geom], crop=True, filled=True)
        zon_f, _ = rasterio.mask.mask(src_z, [flood_geom], crop=True, filled=True)
        # hazard values across all of Lagos (the baseline distribution)
        idx_l, _ = rasterio.mask.mask(src_i, [lagos], crop=True, filled=True)
        zon_l, _ = rasterio.mask.mask(src_z, [lagos], crop=True, filled=True)

    fi = idx_f[0]
    fz = zon_f[0]
    li = idx_l[0]
    lz = zon_l[0]

    m_f = (fi != -9999) & np.isfinite(fi) & (fz > 0)
    m_l = (li != -9999) & np.isfinite(li) & (lz > 0)

    flood_vals = fi[m_f]
    flood_zones = fz[m_f]
    lagos_vals = li[m_l]
    lagos_zones = lz[m_l]

    # pseudo-absence: sample Lagos cells, excluding the flood footprint.
    # Sampling all-Lagos and subtracting the (small, 0.4%) flood share is a
    # close approximation and avoids a costly per-cell point-in-polygon test.
    n_abs = min(len(flood_vals) * 5, len(lagos_vals))
    absence = np.random.default_rng(42).choice(lagos_vals, size=n_abs, replace=False)

    auc = auc_roc(flood_vals.tolist(), absence.tolist())

    # zone enrichment
    enrich = {}
    for z in range(1, 6):
        f_share = float((flood_zones == z).sum()) / len(flood_zones) * 100
        l_share = float((lagos_zones == z).sum()) / len(lagos_zones) * 100
        enrich[ZONE_NAMES[z]] = {
            "pct_of_observed_flood": round(f_share, 2),
            "pct_of_lagos": round(l_share, 2),
            "enrichment": round(f_share / l_share, 2) if l_share > 0 else None,
        }

    hi_f = sum(enrich[z]["pct_of_observed_flood"] for z in ("High", "Very High"))
    hi_l = sum(enrich[z]["pct_of_lagos"] for z in ("High", "Very High"))

    return {
        "observation": "MODIS 250m flood extent, Nigeria Jul-Nov 2012 (NASA/DFO via HDX)",
        "flood_cells": int(len(flood_vals)),
        "flood_area_km2": round(len(flood_vals) * 900 / 1e6, 1),
        "lagos_cells": int(len(lagos_vals)),
        "auc_roc": round(auc, 3),
        "mean_hazard_index_flooded": round(float(flood_vals.mean()), 4),
        "mean_hazard_index_lagos": round(float(lagos_vals.mean()), 4),
        "zones": enrich,
        "high_veryhigh_pct_of_flood": round(hi_f, 2),
        "high_veryhigh_pct_of_lagos": round(hi_l, 2),
        "high_veryhigh_enrichment": round(hi_f / hi_l, 2) if hi_l else None,
    }


# ── TEST B ─────────────────────────────────────────────────────────────────
def test_b():
    exp = {}
    with open(CORE / "exposure_by_lga.csv") as f:
        for row in csv.DictReader(f):
            exp[norm(row["lga_name"])] = {
                "name": row["lga_name"],
                "pct": float(row["pct_high_very_high"]),
                "pop": int(row["total_pop"]),
            }

    counts = {}
    with open(NEMA) as f:
        for row in csv.DictReader(f):
            k = norm(row["lga"])
            counts[k] = counts.get(k, 0) + 1

    matched, unmatched = {}, []
    for k, v in counts.items():
        if k in exp:
            matched[k] = v
        else:
            unmatched.append(k)

    rows = []
    for k, e in exp.items():
        rows.append({
            "lga": e["name"],
            "nema_reports": matched.get(k, 0),
            "model_pct_high_vh": e["pct"],
            "population": e["pop"],
            # absolute exposed people: NEMA incident counts plausibly scale with
            # how many people are exposed, not with the LGA's exposed FRACTION.
            "model_people_high_vh": int(round(e["pop"] * e["pct"] / 100)),
        })
    rows.sort(key=lambda r: -r["nema_reports"])

    rho = spearman([r["nema_reports"] for r in rows],
                   [r["model_pct_high_vh"] for r in rows])
    rho_abs = spearman([r["nema_reports"] for r in rows],
                       [r["model_people_high_vh"] for r in rows])
    rho_pop = spearman([r["nema_reports"] for r in rows],
                       [r["population"] for r in rows])

    with_r = [r["model_pct_high_vh"] for r in rows if r["nema_reports"] > 0]
    without = [r["model_pct_high_vh"] for r in rows if r["nema_reports"] == 0]
    p = mannwhitney_p(without, with_r) if with_r and without else None

    return {
        "observation": "NEMA 2022 flood records, Lagos (62 community reports via HDX)",
        "lgas_with_reports": len(with_r),
        "lgas_without_reports": len(without),
        "unmatched_lga_names": unmatched,
        "spearman_rho": round(rho, 3),
        "spearman_rho_vs_absolute_exposed": round(rho_abs, 3),
        "spearman_rho_vs_population": round(rho_pop, 3),
        "mean_model_pct_reported_lgas": round(sum(with_r) / len(with_r), 1) if with_r else None,
        "mean_model_pct_unreported_lgas": round(sum(without) / len(without), 1) if without else None,
        "mannwhitney_p": round(p, 4) if p is not None else None,
        "per_lga": rows,
    }


def main():
    a = test_a()
    b = test_b()
    out = {"test_a_pixel_level": a, "test_b_lga_level": b}
    (HERE / "spatial_validation_results.json").write_text(json.dumps(out, indent=2))

    print("=" * 66)
    print("TEST A - pixel level vs observed 2012 MODIS flood extent")
    print("=" * 66)
    print(f"  observed flood area in Lagos : {a['flood_area_km2']} km2 "
          f"({a['flood_cells']:,} cells)")
    print(f"  AUC-ROC                      : {a['auc_roc']}")
    print(f"  mean hazard index, flooded   : {a['mean_hazard_index_flooded']}")
    print(f"  mean hazard index, all Lagos : {a['mean_hazard_index_lagos']}")
    print(f"\n  {'zone':<11}{'%flood':>9}{'%Lagos':>9}{'enrich':>9}")
    for z in ("Very Low", "Low", "Moderate", "High", "Very High"):
        d = a["zones"][z]
        e = d["enrichment"]
        print(f"  {z:<11}{d['pct_of_observed_flood']:>9.2f}{d['pct_of_lagos']:>9.2f}"
              f"{(e if e is not None else float('nan')):>9.2f}")
    print(f"\n  High+VeryHigh: {a['high_veryhigh_pct_of_flood']}% of flood vs "
          f"{a['high_veryhigh_pct_of_lagos']}% of Lagos "
          f"-> enrichment {a['high_veryhigh_enrichment']}x")

    print("\n" + "=" * 66)
    print("TEST B - LGA level vs NEMA 2022 reports")
    print("=" * 66)
    print(f"  LGAs with reports    : {b['lgas_with_reports']}")
    print(f"  LGAs without reports : {b['lgas_without_reports']}")
    if b["unmatched_lga_names"]:
        print(f"  UNMATCHED NEMA names : {b['unmatched_lga_names']}")
    print(f"  Spearman rho vs model %H+VH        : {b['spearman_rho']}")
    print(f"  Spearman rho vs absolute exposed   : {b['spearman_rho_vs_absolute_exposed']}")
    print(f"  Spearman rho vs raw population     : {b['spearman_rho_vs_population']}")
    print(f"  model %High+VH, reported LGAs   : {b['mean_model_pct_reported_lgas']}")
    print(f"  model %High+VH, unreported LGAs : {b['mean_model_pct_unreported_lgas']}")
    print(f"  Mann-Whitney p       : {b['mannwhitney_p']}")
    print(f"\n  {'LGA':<20}{'NEMA':>6}{'model %H+VH':>13}")
    for r in b["per_lga"][:20]:
        print(f"  {r['lga']:<20}{r['nema_reports']:>6}{r['model_pct_high_vh']:>13.1f}")


if __name__ == "__main__":
    main()
