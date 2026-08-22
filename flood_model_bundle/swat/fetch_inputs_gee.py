"""
fetch_inputs_gee.py — pull SWAT+ input data for the Ogun lower-reach catchment
==============================================================================
Exports the open datasets your thesis names (§3.3-3.4) from Google Earth Engine,
ready to load into QSWAT+. See SWAT_BUILD_PLAN.md for how these feed the model.

WHAT THIS DOES
  * Static rasters -> Google Drive as GeoTIFF (DEM, slope, WorldCover, SoilGrids)
  * CHIRPS daily rainfall -> per-virtual-station CSV (SWAT precip forcing)
  * MOD16 ET -> monthly catchment-mean CSV (data-scarce calibration target)

WHAT THIS DOES *NOT* DO (get these separately — see SWAT_BUILD_PLAN.md §3)
  * GloFAS reanalysis discharge -> Copernicus CDS (not in GEE)
  * NIHSA / GRDC gauged discharge -> formal data request
  * Temp/solar/wind/RH forcing -> ERA5 (CDS) or SWAT's weather generator

PREREQUISITES
  pip install earthengine-api
  earthengine authenticate         # one-time, needs a free GEE account
  # Exports land in your Google Drive folder 'SWAT_Ogun'.

NOTE: replace the placeholder AOI with your HydroSHEDS-delineated catchment
      polygon for final runs. The bounding box below is a starting extent only.
"""
import ee

# ── study period & area ───────────────────────────────────────────────────────
START, END = "2015-01-01", "2023-12-31"     # adjust to your calibration window
DRIVE_FOLDER = "SWAT_Ogun"
SCALE_DEM = 30            # SRTM native (m)
SCALE_SOIL = 250         # SoilGrids native (m)

# PLACEHOLDER extent: lower Ogun + Lagos Lagoon. REPLACE with delineated basin.
AOI = ee.Geometry.Rectangle([3.05, 6.30, 3.75, 7.20])


def _export_raster(image, name, scale):
    ee.batch.Export.image.toDrive(
        image=image.clip(AOI), description=name, folder=DRIVE_FOLDER,
        fileNamePrefix=name, region=AOI, scale=scale, crs="EPSG:32631",
        maxPixels=1e13,
    ).start()
    print(f"  queued raster: {name}")


def export_static_rasters():
    """DEM, slope, land use, soil — the HRU + delineation inputs."""
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")
    _export_raster(dem, "dem_srtm", SCALE_DEM)
    _export_raster(ee.Terrain.slope(dem), "slope_deg", SCALE_DEM)

    # ESA WorldCover 2021 (v200) — 10 m land cover
    lc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    _export_raster(lc, "worldcover_2021", 10)

    # SoilGrids — VERIFY these asset IDs in the GEE catalog before final runs;
    # ISRIC publishes them as projects/soilgrids-isric/<prop>_mean. SWAT needs
    # texture (sand/clay) + SOC to build the usersoil table.
    for prop in ["sand_mean", "clay_mean", "soc_mean"]:
        try:
            img = ee.Image(f"projects/soilgrids-isric/{prop}").select(0)
            _export_raster(img, f"soilgrids_{prop}", SCALE_SOIL)
        except Exception as e:                       # noqa: BLE001
            print(f"  ! SoilGrids {prop} failed ({e}); confirm asset id manually")


def export_chirps_stations(n_grid=4):
    """CHIRPS daily rainfall as virtual-station CSVs for SWAT precip forcing.
    Builds an n_grid x n_grid lattice of points over the AOI and exports a
    date/precip table per point."""
    chirps = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
              .filterDate(START, END).select("precipitation"))
    b = AOI.bounds().coordinates().get(0).getInfo()
    lons = [p[0] for p in b]; lats = [p[1] for p in b]
    lo_x, hi_x, lo_y, hi_y = min(lons), max(lons), min(lats), max(lats)
    pts = []
    for i in range(n_grid):
        for j in range(n_grid):
            x = lo_x + (hi_x - lo_x) * (i + 0.5) / n_grid
            y = lo_y + (hi_y - lo_y) * (j + 0.5) / n_grid
            pts.append(ee.Feature(ee.Geometry.Point([x, y]),
                                  {"station": f"pcp_{i}{j}"}))
    stations = ee.FeatureCollection(pts)

    def _daily(img):
        d = img.date().format("YYYYMMdd")
        samp = img.reduceRegions(stations, ee.Reducer.first(), 5000)
        return samp.map(lambda f: f.set("date", d))

    table = chirps.map(_daily).flatten()
    ee.batch.Export.table.toDrive(
        collection=table, description="chirps_daily_stations",
        folder=DRIVE_FOLDER, fileFormat="CSV",
        selectors=["station", "date", "precipitation"],
    ).start()
    print("  queued table: chirps_daily_stations")


def export_et_monthly():
    """MOD16 ET, monthly catchment-mean (mm) — the calibration target."""
    et = (ee.ImageCollection("MODIS/061/MOD16A2GF")
          .filterDate(START, END).select("ET"))       # 8-day, scale 0.1 mm

    months = ee.List.sequence(0, ee.Date(END).difference(ee.Date(START), "month").subtract(1))

    def _month(m):
        s = ee.Date(START).advance(m, "month")
        e = s.advance(1, "month")
        # sum of 8-day composites in the month, *0.1 to mm
        val = (et.filterDate(s, e).sum().multiply(0.1)
               .reduceRegion(ee.Reducer.mean(), AOI, 500).get("ET"))
        return ee.Feature(None, {"month": s.format("YYYY-MM"), "et_mm": val})

    table = ee.FeatureCollection(months.map(_month))
    ee.batch.Export.table.toDrive(
        collection=table, description="mod16_et_monthly",
        folder=DRIVE_FOLDER, fileFormat="CSV", selectors=["month", "et_mm"],
    ).start()
    print("  queued table: mod16_et_monthly")


if __name__ == "__main__":
    ee.Initialize()
    print(f"Exporting SWAT+ inputs for Ogun catchment -> Drive/{DRIVE_FOLDER}")
    export_static_rasters()
    export_chirps_stations()
    export_et_monthly()
    print("\nAll tasks queued. Monitor at https://code.earthengine.google.com/tasks")
    print("Replace the placeholder AOI with your delineated catchment before final runs.")
