// ============================================================
// SWAT+ weather for the Ogun basin — paste into the GEE Code Editor
// (https://code.earthengine.google.com/) and click RUN, then run
// the two export tasks that appear under the "Tasks" tab.
// Outputs (to Google Drive / folder "SWAT_Ogun_weather"):
//   ogun_pcp_daily.csv  — daily rainfall (mm) at each subbasin
//   ogun_tmp_daily.csv  — daily tmax/tmin (deg C) at each subbasin
// ============================================================

var START = '2010-01-01';
var END   = '2023-12-31';

// 23 subbasin-centroid stations (lon, lat)
var pts = [
 [1,3.7013,8.8198],[2,3.8483,8.6405],[3,3.5179,8.7137],[4,3.3343,8.4642],
 [5,3.7068,8.5868],[6,3.599,8.4204],[7,3.044,8.0942],[8,3.8119,8.341],
 [9,3.4633,8.2226],[10,3.7292,7.9832],[11,3.2841,8.0229],[12,2.8313,7.7825],
 [13,3.3979,7.9121],[14,3.5679,7.8557],[15,3.3796,7.5765],[16,3.2119,7.6266],
 [17,3.0615,7.535],[18,3.6067,7.4875],[19,3.1729,7.2888],[20,3.3387,7.2617],
 [21,3.344,7.0489],[22,3.1961,6.9233],[23,3.3521,6.7187]
];
var stations = ee.FeatureCollection(pts.map(function(p){
  return ee.Feature(ee.Geometry.Point([p[1],p[2]]), {station: p[0]});
}));

// ---- daily rainfall: CHIRPS (mm/day, ~5.5 km) ----
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterDate(START, END).select('precipitation');

// dedicated rainfall sampler: unmask(0) + explicit output name 'pcp'
var pcpFC = chirps.map(function(img){
  var d = ee.Image(img).date().format('YYYY-MM-dd');
  return img.unmask(0).reduceRegions({
    collection: stations,
    reducer: ee.Reducer.mean().setOutputs(['pcp']),
    scale: 5566
  }).map(function(f){ return f.set('date', d); });
}).flatten();

// ---- daily temperature: ERA5-Land (K -> deg C, ~11 km) ----
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
  .filterDate(START, END)
  .select(['temperature_2m_max','temperature_2m_min'], ['tmax','tmin'])
  .map(function(img){
    return img.subtract(273.15).copyProperties(img, ['system:time_start']);
  });
var tmpFC = era5.map(function(img){
  var d = ee.Image(img).date().format('YYYY-MM-dd');
  return img.reduceRegions({collection: stations, reducer: ee.Reducer.mean(), scale: 11132})
            .map(function(f){ return f.set('date', d); });
}).flatten();

Export.table.toDrive({
  collection: pcpFC, description: 'ogun_pcp_daily', folder: 'SWAT_Ogun_weather',
  fileFormat: 'CSV', selectors: ['station','date','pcp']
});

Export.table.toDrive({
  collection: tmpFC, description: 'ogun_tmp_daily', folder: 'SWAT_Ogun_weather',
  fileFormat: 'CSV', selectors: ['station','date','tmax','tmin']
});

print('Ready — open the Tasks tab (right) and click Run on both exports.');
Map.addLayer(stations, {color:'red'}, 'subbasin stations');
Map.centerObject(stations, 7);
