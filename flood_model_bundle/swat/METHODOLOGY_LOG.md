# SWAT+ Build — Replication Log (Ogun River / Lagos Flood Portal)

A step-by-step, reproducible record of building the SWAT+ hydrological model for the
Ogun River catchment draining into the Lagos Lagoon. Written as a lab-notebook so the
work can be repeated exactly and adapted into thesis Chapter 3 (Methodology).

- **Student:** Attah Gbubemi David
- **Model domain:** Ogun River basin, outlet at Kara/Akute (drains to Lagos Lagoon)
- **Portal / susceptibility map:** statewide Lagos (AHP — pre-existing, separate component)
- **Coordinate system (all layers):** EPSG:32631 (WGS84 / UTM zone 31N)
- **Working folder:** `C:\SWAT_Ogun\`
- **Repo (scripts, data, docs):** `flood_model_bundle/swat/`

---

## 0. Scope decision (why the Ogun, not "Lagos")

SWAT models a **watershed (drainage basin)**, not an administrative area. The floodwater
reaching Lagos via the lagoon falls as rain upstream and flows down the **Ogun River**,
whose catchment (~23,000 km²) extends north of Lagos into Ogun/Oyo States. Modelling the
Ogun basin *is* modelling Lagos's fluvial flood source (thesis §1.5, §3.2 — Ogun is the
"largest contributor of fluvial discharge to the Lagos Lagoon").
Oyan Dam lies in this basin and regulates flow → recorded as a documented limitation.

---

## 1. Software environment

| Component | Version | Notes |
|---|---|---|
| QGIS | **3.44.11 LTR** (64-bit standalone) | install FIRST |
| SWAT+ installer | **4.0.1** (`swatplus-windows-installer-4.0.1.zip`) | installs QSWAT+ 4.0, SWAT+ Editor 4.0, SWAT+ Toolbox 4.0, SWAT+ engine rev 62 |
| GDAL/OGR CLI | bundled in QGIS | `C:\Program Files\QGIS 3.44.11\bin\` |

**Enabling the plugin:** QGIS → Plugins → Manage & Install → Installed → tick **QSWATPlus**.

**Using QGIS's GDAL from a shell** (needed for the commands below) — set:
```
export PROJ_LIB="C:\Program Files\QGIS 3.44.11\share\proj"
export GDAL_DATA="C:\Program Files\QGIS 3.44.11\share\gdal"
GW="/c/Program Files/QGIS 3.44.11/bin/gdalwarp.exe"
O2="/c/Program Files/QGIS 3.44.11/bin/ogr2ogr.exe"
```

---

## 2. Calibration/validation data — river discharge (GEOGLOWS)

**Decision:** NIHSA gauged discharge is slow to obtain and gappy, so we calibrate against
**GEOGLOWS ECMWF modelled daily discharge** — the data-scarce approach justified in the
thesis Ch.2 (Odusanya et al. 2019, satellite/modelled targets where gauges are sparse).
Free, no login, via the GEOGLOWS v2 REST API.

**2.1 Find the river reach from coordinates** (endpoint `getriverid`):
```
curl "https://geoglows.ecmwf.int/api/v2/getriverid?lat=<LAT>&lon=<LON>"
```

**2.2 Identify the Ogun main stem.** Several candidate points were tested; the point that
lands on the main channel (largest mean flow) wins. Result:

| Candidate point | river_id | mean m³/s | max m³/s |
|---|---|---|---|
| Oyan/Abeokuta (7.15N,3.35E) | 140343400 | 0.5 | 41 (tributary) |
| Kara/Akute (6.67N,3.40E) | **140585128** | **216** | **4521** ← CHOSEN outlet reach |
| Lagoon mouth (6.57N,3.43E) | 140506513 | 220 | 4702 (below outlet) |

Reach **140585128** (Kara/Akute) chosen — main stem, just above the lagoon.

**2.3 Download the retrospective daily series** (endpoint `retrospective`, 1940–present):
```
curl "https://geoglows.ecmwf.int/api/v2/retrospective/140585128?format=csv" -o geoglows_ogun_kara_140585128_daily.csv
```
Also aggregated to monthly means (thesis evaluation timestep) → `..._monthly.csv`.

**2.4 Result (sanity check).** 31,589 days, 1940-01-01 → 2026-06-26. Monthly climatology
(mean m³/s) peaks in the flood season — consistent with Lagos flooding:
Jan 72 · Feb 50 · Mar 48 · Apr 70 · May 128 · Jun 237 · Jul 318 · Aug 361 ·
**Sep 531** · Oct 438 · Nov 224 · Dec 119.

Files: `flood_model_bundle/swat/geoglows_ogun_kara_140585128_daily.csv` (+ `_monthly.csv`).
Reusable script: `flood_model_bundle/swat/fetch_geoglows_discharge.py`.

---

## 3. DEM (Copernicus GLO-30, 30 m)

**Source:** Copernicus GLO-30 DEM, AWS open bucket `copernicus-dem-30m` (no login).
Chosen over SRTM because it's fetchable without an Earthdata account and covers the whole
basin (existing SRTM tiles only reached 6–7°N).

**3.1 Download 6 tiles** covering the basin (lat N06–N08 × lon E002–E003):
```
for lat in N06 N07 N08; do for lon in E002 E003; do t="${lat}_00_${lon}_00";
  curl "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_${t}_DEM/Copernicus_DSM_COG_10_${t}_DEM.tif" -o "cop_${t}.tif";
done; done
```

**3.2 Mosaic + reproject to EPSG:32631 @ 30 m** (single DEM for QSWAT+):
```
"$GW" -t_srs EPSG:32631 -tr 30 30 -r bilinear -of GTiff -co COMPRESS=LZW -co TILED=YES \
   cop_N06_00_E002_00.tif cop_N06_00_E003_00.tif cop_N07_00_E002_00.tif \
   cop_N07_00_E003_00.tif cop_N08_00_E002_00.tif cop_N08_00_E003_00.tif \
   ogun_dem_utm31.tif
```
Output: `C:\SWAT_Ogun\DEM\ogun_dem_utm31.tif` — 7379 × 11060 px, 30 m, EPSG:32631 (~280 MB).
Source tiles deleted after mosaicking to save disk.

**3.3 Resample to 90 m for delineation** (the 30 m DEM = 81 M px hung TauDEM's D8FlowDir
for 3.4 h; 90 m is standard for a 23,000 km² basin and runs in minutes):
```
"$GW" -tr 90 90 -r bilinear -of GTiff -co COMPRESS=LZW -co TILED=YES ogun_dem_utm31.tif ogun_dem_90m_utm31.tif
```
Output: `C:\SWAT_Ogun\DEM\ogun_dem_90m_utm31.tif` — 2460 × 3687 px, 90 m (~32 MB).

**3.4 Clip to basin (final DEM for delineation).** The 90 m full-rectangle still included a
large block of flat ocean/lagoon/coastal plain *south of the Kara outlet* that stalled
TauDEM D8FlowDir and crashed the machine. Since the basin drains entirely from north of the
outlet, clip to the basin window (lon 2.6–3.9°E, lat 6.55–9.1°N) — losing nothing:
```
"$GW" -t_srs EPSG:32631 -te 2.6 6.55 3.9 9.1 -te_srs EPSG:4326 -tr 90 90 -r bilinear \
   -co COMPRESS=LZW -co TILED=YES ogun_dem_utm31.tif ogun_dem_90m_clip.tif
```
Output: **`C:\SWAT_Ogun\DEM\ogun_dem_90m_clip.tif`** — 1597 × 3134 px, 90 m (~19 MB, 5 M px).
**THIS is the DEM to delineate with.**

> Troubleshooting note: 30 m (81 M px) hung D8FlowDir ~3.4 h; 90 m full-rectangle crashed the
> laptop (RAM + flat coastal flats). Basin-clipped 90 m is the reliable input. Close other
> heavy apps (browsers, IDE) during delineation on this memory-tight machine.

---

## 4. Outlet point shapefile (Kara/Akute)

Placed programmatically so QSWAT+ snaps to it (instead of hunting for the pixel).
Location: **lon 3.402°E, lat 6.664°N** → EPSG:32631 easting/northing **544432.67, 736623.58**.
Attributes required by QSWAT+: `ID=1, INLET=0, RES=0, PTSOURCE=0`.
```
"$O2" -f "ESRI Shapefile" -s_srs EPSG:4326 -t_srs EPSG:32631 ogun_outlet.shp outlet_wgs84.geojson
```
Output: `C:\SWAT_Ogun\gis\ogun_outlet.shp` (+ .dbf/.prj/.shx).

---

## 5. QSWAT+ project + watershed delineation

**5.1 Project:** QGIS → QSWAT+ (`S+` toolbar icon) → **New Project** → parent `C:\SWAT_Ogun`,
name **`OgunModel`** → accept default SWAT+ database. QSWAT+ creates `C:\SWAT_Ogun\OgunModel\`
with layer groups (Watershed, Landuse, Soil, Slope, Results, Animations).

**5.2 Delineate Watershed dialog:**
- **DEM:** `ogun_dem_90m_utm31.tif` (90 m — see §3.3; the 30 m version hung TauDEM).
- **Burn in existing stream network:** OFF (first pass).
- **Channel threshold:** 73.45 sq km (81,612 cells) — default.
- **Stream threshold:** 734.5 sq km (816,117 cells) — default (→ ~subbasin count TBD).
- **Use an inlets/outlets shapefile:** ON → `C:\SWAT_Ogun\gis\ogun_outlet.shp`.
- **Snap threshold:** 300 m.
- **Number of processes:** 0 (single-process — avoids MPI/TauDEM errors; slower but reliable).
- Sequence: **Create streams** (TauDEM: fill → flow dir → flow accum → streams; ~10–20 min on
  this DEM) → **Review snapped** (confirm 1 outlet on a stream) → **Create watershed** → **OK**.

**Troubleshooting — TauDEM hang (resolved):** first attempt used the 30 m DEM (81 M px);
`D8FlowDir.exe` ran 3.4 h with no progress (QGIS "Not Responding"). Diagnosed by watching the
`Watershed\Rasters\DEM\` folder (no new files after `sd8.tif`) and `Get-Process` (D8FlowDir at
~12,000 s CPU). Killed the process (`Stop-Process -Id <pid> -Force`) and switched to the 90 m
DEM (§3.3). Lesson: match DEM resolution to basin size — 90 m for ~23,000 km².

**5.3 Flat-terrain fix — stream burn-in + corrected outlet (REQUIRED).**
The first successful delineation was hydrologically wrong: on the raw clipped DEM the max flow
accumulation was only **462 km²** (vs the Ogun's ~23,000) — the flat valley disperses D8 flow
instead of concentrating it, so no integrated main channel formed (QSWAT+ warned "only one
stream / one subbasin"). DEM verified clean (100% valid, 0–585 m) → terrain/routing issue, not
a data gap. Fix:

- **Burn-in rivers:** extract HydroRIVERS (from `GBUBEMI.zip`), clip to basin + reproject:
  ```
  unzip -j GBUBEMI.zip "GBUBEMI/HydroRIVERS_v10_af_shp/.../HydroRIVERS_v10_af.*" -d raw
  "$O2" -f "ESRI Shapefile" -spat 2.6 6.55 3.9 9.1 -t_srs EPSG:32631 ogun_rivers_burn.shp raw/HydroRIVERS_v10_af.shp
  ```
  → `C:\SWAT_Ogun\gis\ogun_rivers_burn.shp` (2,701 reaches). HydroRIVERS independently confirms
  **max UPLAND_SKM = 24,816 km²** in the basin (extent is correct).
- **Corrected outlet:** the true main stem runs ~2.3 km west of the first outlet point. Snapped
  the outlet to the nearest HydroRIVERS main-stem vertex (UPLAND_SKM ≥ 3000) to Kara → point
  drains **22,007 km²** → `C:\SWAT_Ogun\gis\ogun_outlet2.shp`.

**Redo delineation with:** DEM `ogun_dem_90m_clip.tif`; **Burn in existing stream network ON**
→ `ogun_rivers_burn.shp`; inlets/outlets = **`ogun_outlet2.shp`**; snap 500; processes 0;
Create streams → Review snapped → Create watershed.

**5.4 Delineation result (SUCCESS).** With burn-in + `ogun_outlet2.shp`, flow accumulation
concentrated correctly (max 462 km² → **20,592 km²**). Create watershed produced:
- **23 subbasins**, **total area 19,915 km²** (matches the Ogun basin).
- Outputs in `OgunModel2\Watershed\Shapes\`: `ogun_dem_90m_clipsubbasins.shp`,
  `...wshed.shp`, streams + channels.
- Extent north to ~8.9°N (headwaters). Outlet on main stem (UTM31 ~542139, 736226).

> Next: re-check GEOGLOWS reach at the final outlet lon/lat (should stay ≈ 140585128) so the
> calibration discharge series matches the SWAT outlet.

---

## 6. Step 3 — HRU inputs (land use + soil)

**Land use** — ESA WorldCover 10 m (AWS `esa-worldcover`, no login), tiles N06E000 + N06E003 →
mosaic/clip/resample to 90 m (`-r mode`) at basin extent → `C:\SWAT_Ogun\landuse\ogun_landuse_90m.tif`.
Basin cover: 43% tree, 23% shrub, 16% crop, 12% grass, 4.5% built. Lookup (WorldCover value →
SWAT+ code, verified against `swatplus_datasets.sqlite`) → `landuse\landuse_lookup.csv`
(10→frst, 20→rngb, 30→rnge, 40→agrl, 50→urml, 60→bsvg, 80→watr, 90→wetl, 95→wetf).

**Soil** — SoilGrids 250 m (ISRIC `/vsicurl/files.isric.org`, no login): sand + clay 0–5 cm for
the basin window → % → USDA texture classification (12 classes) → `C:\SWAT_Ogun\soil\ogun_soil_90m.tif`.
Basin: **88% Sandy Loam, 11% Sandy Clay Loam**. Built a custom SWAT soil DB by cloning the FAO
schema: **`texture_usersoil`** (12 rows; representative HYDGRP/BD/AWC/K/CBN/CLAY-SILT-SAND per
texture) + **`texture_soils`** (SOIL_ID→SNAM) written into the project DB
`C:\SWAT_Ogun\OgunModel2\OgunModel2.sqlite`; lookup also at `soil\soil_lookup.csv`.

**Slope** — derived by QSWAT+ from the DEM.

All three share the DEM grid (EPSG:32631, 90 m, `-te 2.6 6.55 3.9 9.1`). Note: single-layer
representative soils (topsoil texture) — a documented data-scarce simplification.

**6.1 Create HRUs (SUCCESS).** In QSWAT+ Step 2 → Create HRUs: landuse map `ogun_landuse_90m.tif`
+ lookup table `worldcover_landuses`; soil map `ogun_soil_90m.tif`, soil data = **usersoil** →
soil lookup `texture_soils`, usersoil `texture_usersoil`; single slope band `[0,9999]`; Read →
**Filter by landuse, soil, slope**, Percent method, Landuse 10% / Soil 10% (Go after each).

Result: **23 subbasins, 71 channels, 71 LSUs, 243 HRUs** (from 1,971 full).

> **Troubleshooting (resolved):** first HRU attempt failed with *"Internal error: Id 490 has
> not been added to table gis_lsus"* — a degenerate micro-channel from burn-in left
> gis_channels(277) ≠ gis_lsus(276). Fix: re-ran delineation with **Channel threshold raised
> 40→150 km²** (fewer, well-formed channels: 277→71); LSUs then matched and HRUs built cleanly.
> Landuse lookup must be a DB **table** (`worldcover_landuses`), not just the CSV — cloned from
> `Example1_landuses` schema (LANDUSE_ID, SWAT_CODE).

---

## 7. Step 4 — Weather inputs (daily precip + temperature)

Signed up for **Google Earth Engine** (free, noncommercial). Ran `swat/gee_weather.js` in the
Code Editor → daily **CHIRPS rainfall** + **ERA5-Land tmax/tmin**, 2010–2023, sampled at the 23
subbasin centroids → CSVs to Drive → `C:\SWAT_Ogun\weather\`.

- GEE gotcha (fixed): single-band CHIRPS `reduceRegions` returned a null column; fixed with
  `ee.Reducer.mean().setOutputs(['pcp'])` + `unmask(0)`. Temperature (2-band) worked first try.
- Sanity: bimodal SW-Nigeria signal with the **August break** (stn 23, 2020: Jun 371, Aug 16,
  Sep 243 mm). Daily range 0–92 mm.

Converted to **SWAT+ weather files** (`build_weather.py`) → `C:\SWAT_Ogun\weather\climate\`:
23×`.pcp` + 23×`.tmp` + `pcp.cli` + `tmp.cli`, matching the SWAT+ format (Mary_Creek example);
station elevations sampled from the DEM; `nbyr=14, tstep=0`.

---

## 8. Step 5 — First run + baseline evaluation

Weather loaded in SWAT+ Editor: WGN from the global `swatplus_wgn.sqlite` table `wgn_cfsr_world`
(180 MB download, extracted to `C:\SWAT_Ogun\wgn\`; "using observed weather data" ticked →
60 nearby generators); observed = the 23 `.pcp`/`.tmp` stations (solar/wind/humidity = `sim`).
Sim period **2010–2023**, nyskip=1. First run: default yearly print. Enabled **monthly** channel
output by editing `print.prt` (`channel`/`channel_sd` monthly → `y`) and re-running with **"Write
input files" UNCHECKED** (so the edit survives).

**Baseline (uncalibrated) vs GEOGLOWS monthly, outlet cha01, 2011–2023 (155 mo):**
- Sim mean **337** vs obs **226** m³/s. **NSE −0.10, R² 0.51, PBIAS −48.9%**.
- Diagnosis: right seasonal shape (R²≈0.5) but wrong partitioning — wet-season peaks too high
  (surface runoff excess) + dry-season baseflow too weak (Jan–Mar sim ~4 vs obs ~50).

---

## 9. Step 6 — Calibration (COMPLETE — Objective ii met ✅)

**Autonomous calibration.** Ran the SWAT+ exe directly
(`…\SWATPlusEditor\resources\app.asar.unpacked\static\swat_exe\swatplus-62-ifo-win_amd64-Rel.exe`)
against the TxtInOut, driven by `C:\SWAT_Ogun\calib.py` (writes `calibration.cal`, adds it to
`file.cio` "chg" slot 2, runs, scores NSE/R²/PBIAS vs GEOGLOWS monthly at outlet cha01). No GUI.

**Key findings during calibration:**
- Flow is **baseflow-dominated** (surface runoff ~18 mm/yr); default `perco=0.90` drained soil
  water before it could evaporate. **Lowering `perco`→0.30** was the first big lever (NSE −0.10→0.18).
- `esco`/`epco`/`awc`/`revap` were **inert or backwards** in rev-62 (raised water) — abandoned.
- **`petco`→1.20** (PET multiplier, the real ET lever) fixed the volume: PBIAS −30%→+3%, ET
  53%→ realistic. `canmx`→12 (canopy interception) trimmed wet-season peaks.
- Aquifer buffer (`alpha`→0.022, `flo_min`→10, `bf_max`→0.55) restored dry-season baseflow.

**Final calibrated parameter set** (in `calibration.cal`, applied to all HRUs/aquifers):
`perco=0.30 · petco=1.20 · canmx=12 · alpha=0.022 · flo_min=10 · bf_max=0.55`

**Result (monthly discharge vs GEOGLOWS, outlet cha01):**
| Period | NSE | R² | PBIAS |
|---|---|---|---|
| Calibration 2011–17 | 0.41 | 0.56 | +6.1% |
| Validation 2018–23 | **0.57** | **0.64** | −3.2% |
| **Full 2011–23** | **0.51** | **0.61** | **+1.6%** |

All acceptance thresholds met (NSE≥0.50, R²≥0.60, |PBIAS|≤25%); validation > calibration ⇒ not
overfit. Mean sim 222 vs obs 226 m³/s.

---

## 10. Step 7 — Scenarios + portal integration (COMPLETE ✅)

**Scenarios** (autonomous, `C:\SWAT_Ogun\scenario.py` — scales the 23 `pcp*.pcp` files, runs the
calibrated model, restores originals). Outlet discharge:
| Rainfall | Mean m³/s | Δ mean | Peak-month m³/s | Δ peak |
|---|---|---|---|---|
| Baseline | 222 | — | 1420 | — |
| +10% | 257 | +15.5% | 1558 | +9.7% |
| +20% | 292 | +31.3% | 1686 | +18.7% |
| +30% | 328 | +47.6% | 1821 | +28.2% |

Nonlinear amplification (+10% rain → +15% flow) — the process-based advantage over the linear
index. Extreme historical: wettest simulated year = **2019** (mean 308, peak 1053). 2022 shows
near-baseline in rainfall-only SWAT (the 2022 flood was Oyan Dam-release driven — documented).

**Portal integration:**
- Results exported → `models/core/swat_results.json` (calibration, params, monthly hydrograph,
  scenarios, extreme year).
- `model_api.py`: added `swat_available/swat_calibration/swat_scenarios/swat_hydrograph/swat_summary`.
- `app.py`: new **"🌊 Hydrology (SWAT+)"** tab — calibration scorecard, obs-vs-sim hydrograph,
  rainfall-scenario table/chart, extreme-year + Oyan-Dam limitation note.
- Both files `py_compile`-clean.

**SWAT+ COMPONENT COMPLETE** — thesis Objectives (ii) [SWAT+ NSE≥0.5] and (v) [validation]
satisfied; statewide AHP susceptibility + calibrated Ogun SWAT+ streamflow now both live in
the portal.

> Scope of that claim: it is measured against the **thesis objectives**, not against the
> four-point calibration/validation plan proposed to the supervisor. Independent ET and
> spatial validation were still outstanding at this point — see §11, which closes them and
> reports honestly mixed results.

---

## 11. Step 8 — Independent validation (ET + spatial)

Added after calibration to close the gap identified in review: **calibration and
validation both used GEOGLOWS**, split only by time period, so nothing outside GEOGLOWS
had ever checked the model. Two independent tests were added. Scripts and full caveats
live in `swat/validation/` and `validation/`.

### 11.1 ET — a second variable the model was never tuned to

Reference: **TerraClimate `aet`** (Abatzoglou et al. 2018), ~4 km monthly, basin-masked
to the delineated watershed, 155 months (2011–2023). Retrieved via the THREDDS NCSS
endpoint as per-year netCDF subsets (~56 KB each — disk-light). **NCSS returns raw Int16;
`scale_factor = 0.1` must be applied manually.**

> **This is NOT MODIS MOD16.** MOD16 needs an interactive GEE/Earthdata login, and the
> no-login route (ORNL DAAC MODIS REST API) returned HTTP 500 on every endpoint. Say so
> plainly — TerraClimate is a climatic water-balance product, not a satellite retrieval,
> which is a weaker independence claim. `validation/fetch_mod16_et_gee.js` redoes this
> with true satellite ET once you can log in.

| | NSE | R² | PBIAS |
|---|---|---|---|
| Monthly (155 mo) | 0.18 | 0.39 | +12.5% |
| Monthly climatology | 0.29 | 0.76 | +12.3% |

Annual: reference **900** vs SWAT **787 mm/yr**. Volume sits inside the ±25% Moriasi band;
seasonal **dynamics** are weak — SWAT damps the swing (too much dry-season ET, too little
at the peak). Honest verdict: **partial pass**.

### 11.2 Multi-variable calibration probe (why parameters were NOT re-tuned)

`swat/validation/calib_joint.py` scores each run against discharge **and** ET together.

| petco | Discharge NSE / R² / PBIAS | ET NSE / PBIAS | Meets thesis thresholds |
|---|---|---|---|
| **1.20 (incumbent)** | 0.507 / 0.606 / +1.6% | 0.180 / +12.5% | ✅ |
| 1.35 | 0.530 / 0.596 / +15.7% | 0.303 / +6.6% | ❌ R² 0.596 |
| 1.50 | 0.507 / 0.583 / +28.7% | 0.367 / +1.1% | ❌ R² and PBIAS |

ET improves monotonically as discharge degrades — the objectives genuinely conflict. Only
the incumbent meets NSE≥0.50, R²≥0.60, |PBIAS|≤25%, so **the incumbent is retained**.

> **Diagnosis worth defending:** `petco` is pinned at its allowed maximum (1.20 in
> `cal_parms.cal`). Independently, TerraClimate says SWAT ET is ~12.5% too low. Two
> unrelated lines of evidence agree the model wants more ET than the parameter range
> permits. Reaching 1.35/1.50 required temporarily raising that ceiling — **restored
> afterwards** (`cal_parms.cal.bak_joint`).
>
> Note the incumbent margins are **thin**: NSE 0.507 vs 0.50, R² 0.606 vs 0.60. Any change
> to forcing or parameters can drop the model below the thesis thresholds — re-run
> `calib_joint.py` after any edit.

### 11.3 Spatial validation of the AHP hazard map

The statewide AHP map had never been checked against a real flood. Two observations, both
real and sourced — **no points were geocoded or invented**.

**Test A — pixel level** vs MODIS 250 m flood extent, Nigeria Jul–Nov 2012 (NASA/DFO via
HDX). 35.2 km² of observed flood inside Lagos (290 separate patches; permanent water is
masked out, so this is detected flooding, not the lagoon).

- **AUC-ROC 0.62** (0.5 = no skill) — modest but real discrimination.
- Zone enrichment (share of observed flood ÷ share of Lagos area) rises **monotonically**:
  Low 0.52 · Moderate 0.66 · High 1.19 · **Very High 1.61**.
- High+Very High holds 67.1% of observed flood vs 48.9% of Lagos → **1.37× enrichment**.

The map **ranks** hazard in the right order; it does not discriminate sharply.

**Test B — LGA level** vs NEMA 2022 Lagos flood records (62 community reports, 13 LGAs).

- Spearman ρ vs modelled % High+V.High: **−0.45**
- ρ vs absolute exposed population: **+0.17**
- ρ vs **raw population: +0.57**

**Inconclusive — reported as a null result.** Report counts track population far better
than they track hazard, so the dataset measures reporting effort, not flood susceptibility.
Do not present Test B as either support for or refutation of the map.

> Data-quality note: `exposure_by_lga.csv` misspells Badagry as **"Badagary"**; the matcher
> aliases it so the 4 Badagry reports are not silently dropped.

**Limitations to carry into the thesis:** MODIS 250 m is coarse for urban Lagos (street-scale
flooding is invisible — non-detection ≠ no flooding); 2012 is a single event against a static
susceptibility surface; NEMA reporting is effort-biased.

---

## 12. Key reproducibility notes / decisions

- **Everything is EPSG:32631**; keep it consistent or QSWAT+/factor overlays misalign.
- **Discharge is modelled (GEOGLOWS), not gauged** — state this plainly; it's a recognised
  data-scarce method, not a flaw. Report performance at the **monthly** step (Moriasi 2007).
- **Disk-light approach throughout** (machine is disk-constrained): REST/curl over heavy
  package installs; delete intermediate tiles after mosaicking.
- **Oyan Dam** regulation not explicitly modelled → documented limitation.
- Outlet reach id **140585128** ties the SWAT outlet to the exact discharge series used for
  calibration — keep them matched if the outlet ever moves.
