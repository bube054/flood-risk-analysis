# SWAT+ Build Plan — Lagos Flood Portal

**For:** Attah Gbubemi David — flood-risk portal, Lagos State
**Purpose:** close the gap between the thesis (which commits to SWAT+) and the delivered bundle (AHP-only), the honest and feasible way.
**Scope:** ONE representative catchment — the **Ogun River lower reach** draining into Lagos Lagoon (your Ch.3 §3.2 primary target). *Not* all of Lagos.

---

## 0. Why this document exists (read first)

Your thesis makes SWAT+ a hard requirement, not a nice-to-have:

- **Objective (ii):** run SWAT+ for a representative catchment, hitting **NSE ≥ 0.50, R² ≥ 0.60, PBIAS within ±25%**, and produce runoff/streamflow under 3 scenarios (baseline, extreme historical, climate sensitivity).
- **Objective (v):** validation acceptance includes **SWAT NSE ≥ 0.50**.
- **§3.6 Component 2:** SWAT calibrated/validated against available discharge.

The delivered `model_api.py` is an **AHP weighted overlay only**. Its `runoff` factor (`_scs_runoff`, line 167) is a simplified SCS Curve-Number calc — *not* SWAT. There is no soil layer either. So the SWAT+ component genuinely has to be built. This plan does that with the smallest defensible effort.

---

## 1. The honest framing (use this in your defense regardless)

The data reality — which your own §1.6 limitations already state — is that **gauged discharge for Ogun is scarce and gappy** ("records supposed to cover 20 years had gaps of 3–5 years"). This is normal for Nigerian basins and it does **not** invalidate a SWAT+ study. The defensible, literature-backed strategy (already cited in your Ch.2) is:

> **Odusanya et al. (2019):** use **satellite evapotranspiration** for multi-site calibration/validation of SWAT in a data-scarce southwestern Nigerian catchment.

So: calibrate primarily against **satellite ET**, benchmark against **modelled reanalysis discharge (GloFAS)**, and bias-check against whatever partial **NIHSA** discharge you can obtain. Report performance at the **monthly** step (your §3.5.6 / Moriasi et al. 2007). This is a recognised approach — present it as a deliberate data-scarce methodology, not an apology.

---

## 2. Tools (all free)

| Tool | Role |
|------|------|
| **QGIS 3.28+** | GIS host |
| **QSWAT+** plugin + **SWAT+ Editor** | Build & run the model |
| **SWAT+ Toolbox** (or SWAT-CUP / SUFI-2) | Calibration & uncertainty |
| **Python + earthengine-api** | Data acquisition (`swat/fetch_inputs_gee.py`) |
| **Copernicus CDS account** | GloFAS reanalysis discharge |

---

## 3. Data acquisition — what feeds SWAT+

All open; all named in your §3.3–3.4. Companion script `swat/fetch_inputs_gee.py` pulls the ones available in Google Earth Engine.

| Dataset | Source | SWAT+ role | How to get |
|---|---|---|---|
| **DEM** (SRTM 30 m / MERIT-Hydro) | `USGS/SRTMGL1_003` | Watershed + HRU delineation | GEE script |
| **Land use** (ESA WorldCover 10 m) | `ESA/WorldCover/v200` | HRU land-use layer | GEE script |
| **Soil** (SoilGrids 250 m) | `projects/soilgrids-isric/*` | HRU soil layer + usersoil params | GEE script (verify asset IDs) |
| **Rainfall** (CHIRPS daily) | `UCSB-CHG/CHIRPS/DAILY` | Weather forcing (virtual stations) | GEE script → per-station CSV |
| **Temp/solar/wind/RH** | ERA5 / CFSR / SWAT weather generator | Weather forcing | CDS or SWAT WGEN |
| **ET (calibration target)** | MOD16 `MODIS/061/MOD16A2GF` | Calibrate where discharge is sparse | GEE script → monthly basin-mean CSV |
| **Discharge (benchmark)** | **GloFAS** reanalysis (Copernicus CDS) | Pseudo-obs streamflow benchmark | CDS API (not GEE) |
| **Discharge (ground truth)** | **NIHSA** / **GRDC** | Real calibration where available | Formal request |
| **Rivers/basins** | HydroSHEDS / HydroRIVERS | Burn-in streams, outlet placement | hydrosheds.org |

---

## 4. Build workflow (QSWAT+)

1. **Delineate** the Ogun lower-reach catchment from the DEM; burn in HydroSHEDS rivers; set the **outlet** at the Ogun inflow to Lagos Lagoon. Confirm drainage area against literature.
2. **HRUs** = WorldCover land use × SoilGrids soil × slope bands. Use a threshold (e.g. 5/10/10%) to keep HRU count manageable.
3. **Weather:** load CHIRPS virtual-station daily precip; temp/solar/wind/RH from ERA5 or the built-in weather generator (`.wgn`). NiMet monthly for bias-check only.
4. **Baseline run:** multi-year warm-up (≥2 yr) + simulation period. Sanity-check the water balance (ET, surface runoff, water yield).
5. **Calibrate** (SWAT+ Toolbox / SUFI-2) at the **monthly** step. Sensitive params typically: `CN2`, `SOL_AWC`, `ESCO`, `GW_DELAY`, `ALPHA_BF`, `GWQMN`, `CH_N2`, `SURLAG`. Targets: **NSE ≥ 0.50, R² ≥ 0.60, |PBIAS| ≤ 25%** against ET (primary) and GloFAS (benchmark). Split calibration/validation periods.
6. **Scenarios** (your 3 required): (a) **baseline**, (b) **extreme historical** — reforce with the 2022 wet-season rainfall, (c) **climate sensitivity** — scale rainfall ±10/20/30%. Export per-subbasin **runoff depth** and **peak streamflow**.

---

## 5. Portal integration (how SWAT feeds the app)

The point of SWAT here is a **"SWAT-derived runoff indicator"** layer for the AHP overlay (your §3.4 technical scope) and dynamic scenario numbers — *not* to replace the susceptibility map.

1. Export SWAT subbasin runoff/water-yield → join to subbasin polygons → **rasterize** onto the model grid → `models/factors/swat_runoff.tif`.
2. In `model_api.py`, swap the `runoff` factor: replace the `_scs_runoff()` output in `_static_factors()` with the SWAT raster (keep the same normalise → weight pipeline; weight stays 0.12). This is a ~10-line change, thin over the existing API.
3. For the scenario tab, index the SWAT scenario runs by rainfall scale so `scenario_exposure(scale)` reads SWAT runoff instead of the linear rainfall multiplier — giving genuinely process-based scenario deltas.
4. Add a **"Hydrology (SWAT+)"** panel: catchment map, calibration hydrograph (sim vs ET/GloFAS), NSE/R²/PBIAS scorecard, and the 3-scenario runoff/peak-flow bars.

Keep the honesty disclaimer (`CLAUDE.md` §5) visible: SWAT covers *one catchment*; the statewide map remains AHP susceptibility.

---

## 6. Realistic effort

| Phase | Effort |
|---|---|
| Data acquisition (script + CDS/NIHSA requests) | 2–4 days (+ NIHSA lead time) |
| QSWAT+ setup + baseline run | 3–5 days |
| Calibration to targets | 3–7 days (iterative) |
| Scenarios + portal integration | 3–4 days |

**Critical path = discharge/ET data.** Start the NIHSA request and run the GEE script *first* (see companion script).

---

## 7. Immediate next actions

1. Run `swat/fetch_inputs_gee.py` (needs a Google Earth Engine account) to export DEM, land use, soil, CHIRPS, and ET for the catchment.
2. Submit a **NIHSA** discharge data request for the Ogun River (and a free **GRDC** request) in parallel.
3. Register for **Copernicus CDS** and pull GloFAS reanalysis discharge at the Ogun outlet.
4. Install QSWAT+ and delineate the catchment.

Once you have the ET/GloFAS series, I can write the calibration-statistics code (NSE/R²/PBIAS), the rasterisation of SWAT output, and the `model_api.py` integration.
