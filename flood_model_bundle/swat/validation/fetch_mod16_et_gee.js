/**
 * MOD16A2GF basin-mean monthly ET for the Ogun catchment.
 * ========================================================
 *
 * Paste into the Google Earth Engine Code Editor (code.earthengine.google.com)
 * and press Run. Exports one CSV to your Google Drive.
 *
 * WHY YOU NEED TO RUN THIS YOURSELF
 * ---------------------------------
 * MOD16 is only reachable through Google Earth Engine or NASA Earthdata, both
 * of which require an interactive OAuth login. The no-login alternative (ORNL
 * DAAC MODIS REST API) was returning HTTP 500 on every endpoint when the
 * validation was built, so `et_validation.py` fell back to TerraClimate.
 *
 * TerraClimate is a climatic water-balance product, NOT a satellite retrieval.
 * MOD16 is a true satellite ET product and is what Odusanya et al. (2019) used.
 * Running this upgrades the validation from "independent gridded reference" to
 * "independent satellite observation" -- a materially stronger claim, and the
 * one your supervisor actually asked for.
 *
 * AFTER RUNNING
 * -------------
 * 1. Download `mod16_et_ogun_monthly.csv` from Drive.
 * 2. Drop it next to et_validation.py.
 * 3. Run:  python et_validation.py --reference mod16_et_ogun_monthly.csv
 *    (the script reads the MOD16 CSV instead of the TerraClimate netCDFs)
 *
 * NOTE ON UNITS: MOD16A2GF `ET` is 8-day total in 0.1 mm. This script sums the
 * 8-day composites within each month and applies the 0.1 scale factor, giving
 * mm/month -- directly comparable to SWAT+ `basin_wb_mon.txt` column `et`.
 */

// ── Basin geometry ─────────────────────────────────────────────────────────
// Bounding box of the delineated SWAT+ watershed (see METHODOLOGY_LOG sec.3.4).
// For an exact basin mean, upload ogun_dem_90m_clipwshed.shp as a GEE asset
// and replace this rectangle with: ee.FeatureCollection('users/<you>/ogun_wshed')
var AOI = ee.Geometry.Rectangle([2.6, 6.55, 3.9, 9.1]);

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

  // Sum the 8-day composites falling in this month, then apply 0.1 scale.
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

print('First 5 months (check these are sane, ~40-120 mm):', monthly.limit(5));

Export.table.toDrive({
  collection: monthly,
  description: 'mod16_et_ogun_monthly',
  fileNamePrefix: 'mod16_et_ogun_monthly',
  fileFormat: 'CSV',
  selectors: ['month', 'mod16_et_mm']
});
