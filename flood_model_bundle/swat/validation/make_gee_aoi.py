"""
Generate fetch_mod16_et_gee.js with the real basin outline inlined.
===================================================================

WHY
---
The first version of the GEE script used a bounding box around the catchment.
That was wrong enough to matter: the rectangle is 40,397 km2 against the basin's
19,915 km2, so about HALF of every sampled pixel lay outside the watershed and
the basin-mean ET was diluted by land that does not drain to the outlet.

Uploading the shapefile as a GEE asset would fix it, but that needs an
interactive login and asset management. Inlining a simplified outline avoids
that entirely -- the script stays copy-paste-and-run.

SIMPLIFICATION
--------------
500 m tolerance takes the dissolved watershed from 7,252 vertices to ~303 while
changing area by 0.03%. Coordinates are rounded to 4 dp (~11 m), far finer than
the 500 m MODIS pixel, so the rounding is invisible to the result.

Run:  python make_gee_aoi.py
"""


from pathlib import Path

import geopandas as gpd

HERE = Path(__file__).resolve().parent
WSHED = Path(r"C:\SWAT_Ogun\OgunModel2\Watershed\Shapes\ogun_dem_90m_clipwshed.shp")
OUT = HERE / "fetch_mod16_et_gee.js"

TOLERANCE_M = 500
DECIMALS = 4


def basin_coords():
    w = gpd.read_file(WSHED)
    dissolved = w.to_crs("EPSG:32631").union_all()
    simplified = dissolved.simplify(TOLERANCE_M)

    area_raw = dissolved.area / 1e6
    area_sim = simplified.area / 1e6
    err = 100 * abs(area_sim - area_raw) / area_raw

    geo = gpd.GeoSeries([simplified], crs="EPSG:32631").to_crs(4326).iloc[0]
    if geo.geom_type != "Polygon":
        raise SystemExit(f"Expected a single Polygon, got {geo.geom_type}.")

    pts = [(round(x, DECIMALS), round(y, DECIMALS)) for x, y in geo.exterior.coords]
    # rounding can collapse neighbours onto each other; drop the duplicates
    ded = [pts[0]] + [c for prev, c in zip(pts, pts[1:]) if c != prev]
    return ded, area_raw, area_sim, err


HEADER = '''/**
 * MOD16A2GF basin-mean monthly ET for the Ogun catchment.
 * ========================================================
 *
 * Paste into the Google Earth Engine Code Editor (code.earthengine.google.com)
 * and press Run, then run the export task that appears under the Tasks tab.
 * Exports one CSV to your Google Drive.
 *
 * WHY YOU NEED TO RUN THIS YOURSELF
 * ---------------------------------
 * MOD16 is reachable only through Google Earth Engine or NASA Earthdata, both
 * of which require an interactive OAuth login. It cannot be run headlessly.
 *
 * THE AOI IS THE REAL BASIN, NOT A BOUNDING BOX
 * ---------------------------------------------
 * An earlier version used a rectangle around the catchment. That was wrong
 * enough to matter: the rectangle is 40,397 km2 against the basin's {area_raw:,.0f}
 * km2, so roughly HALF of every sampled pixel lay outside the watershed and the
 * basin-mean ET was diluted by land that does not drain to the outlet.
 *
 * The polygon below is the delineated SWAT+ watershed (ogun_dem_90m_clipwshed
 * .shp, 71 subbasins dissolved), reprojected to WGS84 and simplified with a
 * {tol} m tolerance: {n} vertices, area error {err:.3f}% ({area_raw:,.0f} ->
 * {area_sim:,.0f} km2). Inlining it avoids uploading a GEE asset at all.
 *
 * DO NOT EDIT THE COORDINATES BY HAND -- regenerate with:
 *     python make_gee_aoi.py
 *
 * UNITS: MOD16A2GF `ET` is an 8-day total in 0.1 mm. This sums the 8-day
 * composites within each month and applies the 0.1 scale, giving mm/month --
 * directly comparable to SWAT+ `basin_wb_mon.txt` column `et`.
 *
 * AFTER RUNNING
 * -------------
 * 1. Download `mod16_et_ogun_monthly_basin.csv` from Drive.
 * 2. Put it in flood_model_bundle/swat/validation/.
 * 3. Run: python et_validation.py --reference mod16_et_ogun_monthly_basin.csv
 */

// ── Basin geometry: delineated Ogun watershed ({n} vertices, WGS84) ─────────
var AOI = ee.Geometry.Polygon([[
'''

FOOTER = ''']], null, false);   // geodesic=false: treat edges as planar lat/lon

var START = '2011-01-01';
var END   = '2023-12-31';

// ── MOD16A2GF: gap-filled 8-day ET, 500 m ──────────────────────────────────
var et8 = ee.ImageCollection('MODIS/061/MOD16A2GF')
            .filterDate(START, END)
            .select('ET');

// ── Aggregate 8-day composites to monthly totals ───────────────────────────
var months = ee.List.sequence(0, ee.Date(END).difference(ee.Date(START), 'month').floor());

var monthly = ee.FeatureCollection(months.map(function (i) {
  var start = ee.Date(START).advance(i, 'month');
  var end   = start.advance(1, 'month');

  // Sum the 8-day composites falling in this month, then apply the 0.1 scale.
  var total = et8.filterDate(start, end).sum().multiply(0.1);

  var mean = total.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: AOI,
    scale: 500,
    maxPixels: 1e13,
    bestEffort: true
  }).get('ET');

  return ee.Feature(null, {
    month: start.format('YYYY-MM'),
    mod16_et_mm: mean
  });
}));

// Visual check: the red outline must trace the Ogun basin, not a rectangle.
Map.centerObject(AOI, 7);
Map.addLayer(AOI, {color: 'red'}, 'Ogun basin (AOI)');

print('Basin area km2 (expect ~19,900):', AOI.area(1000).divide(1e6));
print('First 5 months (expect ~30-120 mm):', monthly.limit(5));

Export.table.toDrive({
  collection: monthly,
  description: 'mod16_et_ogun_monthly_basin',
  fileNamePrefix: 'mod16_et_ogun_monthly_basin',
  fileFormat: 'CSV',
  selectors: ['month', 'mod16_et_mm']
});
'''


def wrap_tokens(tokens, width=92, indent="  "):
    """Join tokens with commas, wrapping at `width` WITHOUT ever splitting one.

    textwrap.wrap is unusable here: the joined string contains no spaces, so
    break_long_words chops through the middle of coordinate literals and emits
    JavaScript that will not parse.
    """
    lines, cur = [], ""
    for i, tok in enumerate(tokens):
        piece = tok + ("," if i < len(tokens) - 1 else "")
        if cur and len(cur) + len(piece) > width:
            lines.append(indent + cur)
            cur = piece
        else:
            cur += piece
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)


def main():
    pts, area_raw, area_sim, err = basin_coords()
    tokens = [f"[{x},{y}]" for x, y in pts]
    wrapped = wrap_tokens(tokens)

    js = HEADER.format(n=len(pts), tol=TOLERANCE_M, err=err,
                       area_raw=area_raw, area_sim=area_sim) + wrapped + "\n" + FOOTER
    # utf-8 explicitly: the header uses box-drawing characters that Windows'
    # default cp1252 codec cannot encode.
    OUT.write_text(js, encoding="utf-8", newline="\n")

    print(f"vertices     : {len(pts)}")
    print(f"area raw     : {area_raw:,.0f} km2")
    print(f"area simplif.: {area_sim:,.0f} km2  (error {err:.3f}%)")
    print(f"wrote        : {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
