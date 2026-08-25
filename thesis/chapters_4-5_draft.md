# **CHAPTER FOUR**

# **RESULTS AND DISCUSSION**

## **4.1 Introduction**

This chapter presents the results obtained from the methodology set out in Chapter Three and discusses their implications. The presentation follows the order of the specific objectives stated in Section 1.3: the assembled data stack (Section 4.2), the SWAT+ hydrological model for the Ogun catchment together with its calibration, validation and scenario runs (Section 4.3), an independent multi-variable check of that model against satellite evapotranspiration (Section 4.4), the AHP-based flood susceptibility and risk maps (Section 4.5), the spatial validation of those maps against observed flood records (Section 4.6), and the interactive web portal (Section 4.7). Section 4.8 assesses each objective against the acceptance criteria defined in Table 3.6, and Section 4.9 discusses the wider meaning of the findings.

Results are reported as obtained. Where an acceptance criterion was not met, this is stated explicitly and the likely cause is examined rather than set aside. Two components of the study met their thresholds and one did not; that mixed outcome is itself a substantive finding and is treated as such.

## **4.2 Assembled Data Stack**

All layers listed in Section 3.3 were acquired, harmonised to EPSG:32631 and clipped to their respective study extents. Table 4.1 summarises the final data stack together with the deviations from the sources originally proposed.

**Table 4.1:** Final data stack and deviations from the proposed sources

| Layer | Source used | Resolution | Deviation from Section 3.3 |
|---|---|---|---|
| Rainfall (SWAT forcing) | CHIRPS daily | 5 km, 23 virtual stations | As proposed |
| Temperature | ERA5-Land daily tmax/tmin | 9 km | As proposed |
| Rainfall (statistics) | NiMet Ikeja gauge, 1996–2025 | Station | As proposed |
| DEM | **Copernicus GLO-30** | 30 m (resampled to 90 m) | **SRTM replaced** |
| Rivers/basins | HydroRIVERS v1.0 | Vector | As proposed |
| Land cover | ESA WorldCover v200 | 10 m (resampled to 90 m) | As proposed |
| Soil | SoilGrids 250 m, sand/clay 0–5 cm | 250 m (resampled to 90 m) | Single-layer texture only |
| Discharge | **GEOGLOWS v2, reach 140585128** | Daily, 1940–2026 | **NIHSA gauge replaced** |
| Flood inventory | MODIS 250 m flood extent 2012; NEMA 2022 records | 250 m / LGA | **Compiled from open archives** |
| Population | WorldPop | 100 m | As proposed |

Two deviations require justification.

The Copernicus GLO-30 DEM replaced SRTM because the available SRTM tiles did not extend beyond 7°N and therefore did not cover the northern headwaters of the Ogun basin, which reaches approximately 8.95°N. Copernicus GLO-30 offered equivalent resolution with complete basin coverage and open access without registration.

Observed discharge from NIHSA could not be obtained within the project period. This limitation was anticipated in Section 1.6, which records that available gauge series for the Ogun contained gaps of three to five years. GEOGLOWS ECMWF retrospective discharge was adopted in its place, following the data-scarce calibration strategy documented in Chapter Two. The implications of calibrating against a modelled rather than gauged reference are examined in Section 4.9.2.

## **4.3 SWAT+ Hydrological Model for the Ogun Catchment**

### **4.3.1 Catchment Delineation and HRU Definition**

Delineation from the 90 m conditioned DEM with the HydroRIVERS network burned in produced a catchment of **19,915 km²** discharging at the Kara/Akute outlet (UTM 31N 542139 E, 736226 N), divided into **23 subbasins**. This compares with an independent HydroRIVERS upstream-area estimate of 24,816 km² for the basin as a whole and confirms that the delineated extent represents the Ogun system draining to the Lagos Lagoon.

An initial delineation attempt without stream burn-in produced a maximum flow accumulation of only 462 km². The flat valley terrain dispersed the D8 flow routing so that no integrated main channel formed. Burning in the HydroRIVERS network and relocating the outlet to the nearest main-stem vertex raised maximum flow accumulation to 20,592 km², resolving the problem. This is recorded because it is a common and easily misdiagnosed failure mode in low-relief tropical catchments.

HRU definition used a 10% land-use and 10% soil threshold with a single slope band, producing **71 channels, 71 landscape units and 243 HRUs** from 1,971 candidate combinations. Basin land cover was 43% tree, 23% shrub, 16% cropland, 12% grassland and 4.5% built-up. Basin soils were dominated by two textures, **88% sandy loam and 11% sandy clay loam**, represented through a custom user-soil database built on the FAO schema.

### **4.3.2 Baseline (Uncalibrated) Performance**

The uncalibrated model was run for 2010–2023 with a one-year warm-up and evaluated at the monthly time step against GEOGLOWS discharge at the outlet for 2011–2023 (155 months). Simulated mean discharge was **337 m³/s** against an observed mean of **226 m³/s**, giving **NSE −0.10, R² 0.51 and PBIAS −48.9%**.

The combination of a moderate R² with a strongly negative NSE and large negative bias indicates that the model reproduced the seasonal shape of the hydrograph but partitioned water incorrectly: wet-season peaks were substantially overestimated while dry-season baseflow was severely underestimated, with simulated January–March flows of approximately 4 m³/s against observed values near 50 m³/s.

### **4.3.3 Calibration and Validation**

Calibration proceeded by direct manipulation of `calibration.cal` and repeated execution of the SWAT+ engine, with each candidate parameter set scored against monthly GEOGLOWS discharge. Four findings shaped the final parameter set.

First, flow in this catchment proved **baseflow-dominated**, with surface runoff contributing approximately 18 mm/yr. The default percolation factor of 0.90 drained soil water before it could be returned to the atmosphere; reducing `perco` to 0.30 produced the first substantial improvement, raising NSE from −0.10 to 0.18.

Second, the PET multiplier `petco` proved to be the effective control on water balance. Raising it to **1.20** moved PBIAS from −30% to +3% and brought the simulated evapotranspiration fraction to a realistic level.

Third, canopy interception (`canmx` = 12 mm) trimmed the excessive wet-season peaks.

Fourth, aquifer parameters (`alpha` = 0.022, `flo_min` = 10, `bf_max` = 0.55) restored dry-season baseflow.

The final calibrated parameter set was therefore `perco` 0.30, `petco` 1.20, `canmx` 12, `alpha` 0.022, `flo_min` 10 and `bf_max` 0.55, applied uniformly across all HRUs and aquifers. Table 4.2 reports performance under the split-sample scheme.

**Table 4.2:** SWAT+ monthly discharge performance at the Ogun outlet

| Period | NSE | R² | PBIAS |
|---|---|---|---|
| Calibration, 2011–2017 | 0.41 | 0.56 | +6.1% |
| Validation, 2018–2023 | **0.57** | **0.64** | −3.2% |
| Full period, 2011–2023 | **0.507** | **0.606** | **+1.6%** |

Full-period performance satisfies all three acceptance criteria of Table 3.6 (NSE > 0.50, R² > 0.60, |PBIAS| < 25%), and Objective (ii) is therefore met. Simulated mean discharge of 222 m³/s compares with 226 m³/s observed.

Two features of Table 4.2 warrant comment. Validation performance **exceeds** calibration performance on every metric, which indicates that the parameter set is not over-fitted to the calibration window — an encouraging result given that the calibration was conducted manually rather than through automated optimisation. Conversely, the full-period margins are **narrow**: NSE exceeds its threshold by 0.007 and R² by 0.006. The model is therefore satisfactory but only marginally so, and any change to forcing data or parameters would require the evaluation to be repeated before the thresholds could still be claimed.

Monthly climatology (Table 4.3) shows the model reproducing the timing of the flood season, including the September peak that drives fluvial flooding into the Lagos Lagoon.

**Table 4.3:** Observed and simulated monthly discharge climatology (m³/s), 2011–2023

| Month | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Observed | 69 | 47 | 42 | 59 | 90 | 184 | 328 | 332 | 684 | 518 | 235 | 116 |
| Simulated | 44 | 26 | 14 | 13 | 23 | 115 | 312 | 363 | 760 | 720 | 196 | 72 |

The model captures the September maximum but overestimates October discharge (720 against 518 m³/s) and continues to underestimate the February–May transition, indicating that recession from the wet season is too slow and the early rains generate too little flow.

### **4.3.4 Scenario Simulations**

Three scenario families required by Objective (ii) were run using the calibrated model. Rainfall scenarios were produced by scaling all 23 precipitation input files.

**Table 4.4:** Simulated outlet discharge under rainfall scenarios

| Scenario | Mean (m³/s) | Δ mean | Peak month (m³/s) | Δ peak |
|---|---|---|---|---|
| Baseline | 222 | — | 1420 | — |
| +10% rainfall | 257 | +15.5% | 1558 | +9.7% |
| +20% rainfall | 292 | +31.3% | 1686 | +18.7% |
| +30% rainfall | 328 | +47.6% | 1821 | +28.2% |

The response is **non-linear**: a 10% increase in rainfall produces a 15.5% increase in mean discharge, and a 30% increase produces a 47.6% increase. This amplification is the principal analytical advantage of a process-based model over the linear rainfall term embedded in the susceptibility index, and it indicates that catchment response to intensifying rainfall cannot be estimated by proportional scaling.

For the extreme historical scenario, the wettest simulated year was **2019** (annual mean 308 m³/s, peak month 1053 m³/s). The 2022 flood year, which produced severe flooding nationally, returned near-baseline discharge in the rainfall-only simulation. This is consistent with documented evidence that the 2022 event in this basin was driven substantially by Oyan Dam releases rather than by rainfall alone. Since reservoir operation is not represented in the model, the 2022 event lies outside its representational scope, and this is recorded as a limitation in Section 5.4.

## **4.4 Independent Validation of the Hydrological Model**

### **4.4.1 Rationale**

The calibration reported in Section 4.3.3 used GEOGLOWS discharge for both the calibration and validation periods, separated only in time. No dataset outside GEOGLOWS had tested the model. Following the multi-variable approach of Odusanya *et al.* (2019), an independent check was therefore performed against **evapotranspiration**, a variable that entered no part of the objective function. Agreement on ET is consequently an out-of-sample test rather than a fitted result.

Two unrelated reference products were used: **MODIS MOD16A2GF** (satellite retrieval, 500 m, 8-day composites aggregated to monthly) as the primary reference, and **TerraClimate** actual evapotranspiration (climatic water balance, approximately 4 km monthly) as a corroborating second reference. Both were sampled over the delineated 19,915 km² basin outline for 155 months (2011–2023).

### **4.4.2 Results**

**Table 4.5:** SWAT+ simulated evapotranspiration against two independent references

| Reference | Monthly NSE | R² | PBIAS | Annual mean (mm/yr) |
|---|---|---|---|---|
| MODIS MOD16A2GF | 0.14 | 0.36 | +14.4% | 920 |
| TerraClimate AET | 0.18 | 0.39 | +12.5% | 900 |
| SWAT+ simulated | — | — | — | **787** |

Annual volume falls within the ±25% Moriasi band against both references. Monthly agreement is weak. The reason is visible in the seasonal cycle (Table 4.6).

**Table 4.6:** Monthly evapotranspiration climatology (mm), MODIS against SWAT+

| Month | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MODIS | 27.8 | 32.1 | 53.7 | 65.0 | 87.0 | 101.7 | 110.2 | 112.3 | 113.6 | 88.5 | 83.2 | 41.9 |
| SWAT+ | 55.9 | 49.8 | 59.5 | 64.9 | 75.6 | 68.8 | 67.9 | 65.4 | 70.7 | 73.8 | 72.0 | 63.0 |

MODIS evapotranspiration varies across an annual range of approximately **86 mm**; the simulated series varies across approximately **26 mm**. The model therefore reproduces roughly the correct annual quantity of water returned to the atmosphere but distributes it far too evenly through the year, generating excess evapotranspiration in the dry season and a substantial deficit at the wet-season maximum.

That two independent products — one a satellite retrieval, the other a water-balance model — agree both with each other and on the direction of the discrepancy indicates that this is a property of the hydrological model rather than an artefact of a single reference dataset.

### **4.4.3 Multi-Variable Calibration Trade-off**

Whether the parameter set could be adjusted to improve evapotranspiration was tested directly by scoring candidate sets against discharge and ET simultaneously.

**Table 4.7:** Simultaneous discharge and ET performance across `petco` values

| `petco` | Discharge NSE | Discharge R² | Discharge PBIAS | ET NSE | ET PBIAS | Meets Table 3.6 |
|---|---|---|---|---|---|---|
| **1.20 (adopted)** | 0.507 | 0.606 | +1.6% | 0.14 | +14.4% | **Yes** |
| 1.35 | 0.530 | 0.596 | +15.7% | 0.30 | +6.6% | No (R²) |
| 1.50 | 0.507 | 0.583 | +28.7% | 0.37 | +1.1% | No (R², PBIAS) |

Evapotranspiration improves monotonically as `petco` rises, while discharge performance degrades below the thresholds the study is required to meet. The two objectives are in direct conflict, and the adopted parameter set is the only one of those tested that satisfies the discharge criteria. It was therefore retained.

The diagnosis is that `petco` is **pinned at its permitted maximum of 1.20** in the SWAT+ parameter database. Independently, both ET references indicate that simulated evapotranspiration is 12–14% too low. Two separate lines of evidence thus converge on the same conclusion: the model requires more evapotranspiration than the parameter range allows. Values of 1.35 and 1.50 were reachable only by temporarily raising that ceiling, which was restored afterwards.

## **4.5 Flood Susceptibility and Risk Mapping**

### **4.5.1 AHP Weights**

Eight conditioning factors were combined by weighted linear overlay using the AHP weights in Table 4.8.

**Table 4.8:** AHP weights for the flood susceptibility index

| Factor | Weight |
|---|---|
| Elevation | 0.20 |
| Topographic Wetness Index | 0.18 |
| Distance to rivers | 0.15 |
| Flow accumulation | 0.12 |
| Runoff (SCS-CN) | 0.12 |
| Slope | 0.10 |
| Extreme rainfall | 0.08 |
| Land use / land cover | 0.05 |
| **Total** | **1.00** |

*[Insert the consistency ratio from your pairwise comparison matrix here. Section 3.6.3 requires CR ≤ 0.10, and the matrix itself should appear as an appendix.]*

The weighting is dominated by terrain: elevation and TWI together account for 0.38 of the index, while the two rainfall-driven components (runoff and extreme rainfall) account for 0.20. The resulting map is consequently structured principally by topography. This is a deliberate consequence of the weighting rather than a defect, but it has direct implications for the validation results in Section 4.6 and is returned to in Section 4.9.3.

### **4.5.2 Susceptibility Classes and Population Exposure**

The flood susceptibility index was classified into five zones at equal intervals. Table 4.9 reports the area and resident population of each.

**Table 4.9:** Susceptibility zone areas and population exposure, Lagos State

| Zone | Area (km²) | % of Lagos | Population | % of population |
|---|---|---|---|---|
| Very Low | 0.8 | 0.02 | 10,077 | 0.08 |
| Low | 169.5 | 4.46 | 692,475 | 5.58 |
| Moderate | 2,309.9 | 46.61 | 6,908,435 | 55.62 |
| High | 3,381.0 | 27.92 | 4,368,569 | 35.17 |
| Very High | 799.0 | 20.99 | 441,500 | 3.55 |

**4,810,069 residents — 38.7% of the state population — fall within the High or Very High zones.** At LGA level, exposure ranges from 67.8% of the population in Eti-Osa and 65.0% in Lagos Island down to 7.2% in Ifako/Ijaye and 9.9% in Agege. The pattern follows the coastal and lagoon-adjacent low-lying belt, consistent with the terrain-dominated weighting.

### **4.5.3 Rainfall Frequency Analysis**

Gumbel analysis of the NiMet Ikeja annual maximum series (1996–2025; mean annual rainfall 1,821.8 mm) produced the return levels in Table 4.10 (μ = 1582.4, β = 414.8).

**Table 4.10:** Gumbel design rainfall, Ikeja

| Return period (yr) | 2 | 5 | 10 | 25 | 50 | 100 |
|---|---|---|---|---|---|---|
| Design rainfall (mm) | 1,734 | 2,205 | 2,516 | 2,909 | 3,201 | 3,490 |

The observed maximum of 3,931.7 mm (2018) corresponds to a return period of approximately 289 years on this fit, indicating either an exceptional event or that the Gumbel distribution understates the upper tail for this station. Mann–Kendall testing found **no significant trend** in annual rainfall (Z = 0.18, p = 0.86) but a **significant increasing trend in mean temperature** (Z = 4.17, p < 0.001, +0.44 °C/decade).

## **4.6 Spatial Validation of the Susceptibility Map**

### **4.6.1 Validation Data**

No comprehensive spatial flood database exists for Lagos. Two independent observational datasets were compiled from open archives:

1. **MODIS 250 m flood extent, Nigeria, July–November 2012** (NASA/DFO, via HDX). Within Lagos this comprises **35.2 km² across 290 discrete patches**. Permanent water bodies are masked in the source product, so the extent represents detected flooding rather than the lagoon system.
2. **NEMA 2022 flood records** (via HDX): **62 community-level reports across 13 of the 20 Lagos LGAs**.

No geocoding of NEMA community names was attempted. Assigning coordinates to place names would introduce fabricated locations into the very dataset used for validation, so the NEMA records were used only at the LGA level of aggregation that the source supports.

### **4.6.2 Overlay Analysis**

**Table 4.11:** Distribution of observed 2012 flood extent across susceptibility zones

| Zone | % of observed flood | % of Lagos area | Enrichment |
|---|---|---|---|
| Very Low | 0.00 | 0.02 | 0.00 |
| Low | 2.32 | 4.46 | 0.52 |
| Moderate | 30.61 | 46.61 | 0.66 |
| High | 33.19 | 27.92 | **1.19** |
| Very High | 33.89 | 20.99 | **1.61** |
| **High + Very High** | **67.08** | **48.91** | **1.37** |

Enrichment — the share of observed flooding in a zone divided by that zone's share of the state — rises **monotonically** across the five classes. Observed flooding is 1.61 times more concentrated in the Very High zone than chance would produce, and correspondingly depleted in the Low and Moderate zones. The map therefore orders flood susceptibility correctly.

The enrichment ratio rather than the raw percentage is the meaningful statistic here. The High and Very High zones jointly cover 48.9% of Lagos, so a map assigning zones at random would place approximately 49% of observed flooding in them. The measured 67.1% represents a genuine but moderate improvement on chance.

### **4.6.3 Discriminatory Power and Confusion Matrix**

AUC-ROC was computed by comparing FSI values at flood-affected cells against a random sample of non-flood cells, yielding **AUC-ROC = 0.62**. On the interpretation scale adopted in Section 3.8.2 this falls below the 0.70 threshold for acceptable discrimination, though above 0.50, which would indicate no discrimination at all.

At the Youden-optimal threshold (FSI = 0.596) the confusion matrix is:

**Table 4.12:** Confusion matrix at the Youden-optimal threshold

| | Predicted flood | Predicted non-flood |
|---|---|---|
| **Observed flood** | TP = 26,799 | FN = 12,309 |
| **Observed non-flood** | FP = 98,888 | TN = 96,652 |

Sensitivity = **0.685**; specificity = **0.494**; overall accuracy = **0.526**; precision = **0.213**.

Specificity close to 0.50 combined with precision of 0.21 identifies the mechanism directly: because the High and Very High zones occupy nearly half the state, they capture flooded and non-flooded ground at close to the same rate. The map succeeds at ranking relative susceptibility and fails at separating flooded from non-flooded locations at any single threshold.

### **4.6.4 LGA-Level Comparison with NEMA Records**

**Table 4.13:** Spearman rank correlation between NEMA report counts and modelled quantities

| Compared quantity | Spearman ρ |
|---|---|
| Modelled % population in High + Very High | **−0.45** |
| Modelled absolute population exposed | +0.17 |
| **Raw LGA population** | **+0.57** |

NEMA report counts correlate more strongly with raw population than with any modelled exposure quantity. The dataset therefore predominantly records where people and reporting capacity are concentrated rather than where flooding occurs, and it cannot validate the susceptibility map in either direction. The Mann–Whitney comparison between LGAs with and without reports was not significant (p = 0.10). **This test is reported as inconclusive.**

The negative correlation against exposure fraction is nonetheless worth noting as a hypothesis rather than a finding. The LGAs generating the most reports — Alimosho (11), Ikorodu (10), Agege (5) and Ifako/Ijaye (3) — rank low in the model, at 14.4%, 22.4%, 9.9% and 7.2% respectively. These are dense inland areas where flooding is commonly attributed to drainage failure and blocked channels rather than to terrain position. A terrain-weighted index would not be expected to capture such flooding, and this possibility is examined in Section 4.9.3.

## **4.7 Interactive Web Portal**

A functional portal was delivered providing eight views: project overview, hazard map, point query, exposure dashboard, rainfall scenario runner, climate panel, SWAT+ hydrology panel and validation panel. All five core features required by Objective (iv) are present: layer control with legends, a time-series dashboard, a scenario runner, spatial query popups and downloadable outputs.

The implementation stack differs from that specified in Objective (iv). The portal was built as a **Streamlit** application over a single Python API module (`model_api.py`), with Folium/Leaflet providing the interactive map. It does not use PostgreSQL/PostGIS, GeoServer, FastAPI, React or Docker.

This substitution was made because the analytical outputs are static raster and tabular products that do not require a spatial database or tile server, and because a single-process application was deployable on the available hardware without container orchestration. The functional requirements of Objective (iv) are satisfied; the architectural specification is not. Section 5.4 records this as a departure from the stated methodology, and Section 5.5 recommends how the objective should be reworded or the architecture completed.

## **4.8 Attainment of Objectives Against Acceptance Criteria**

**Table 4.14:** Attainment against the acceptance criteria of Table 3.6

| Component | Metric | Criterion | Achieved | Status |
|---|---|---|---|---|
| SWAT+ | NSE | > 0.50 | 0.507 | **Met** |
| SWAT+ | R² | > 0.60 | 0.606 | **Met** |
| SWAT+ | PBIAS | < ±25% | +1.6% | **Met** |
| SWAT+ | P-factor | ≥ 0.70 | Not computed | **Not assessed** |
| SWAT+ | R-factor | ≤ 1.5 | Not computed | **Not assessed** |
| Susceptibility | AUC-ROC | > 0.70 | 0.62 | **Not met** |
| Susceptibility | Sensitivity | ≥ 0.70 | 0.685 | **Not met** |
| Susceptibility | Overall accuracy | > 0.70 | 0.526 | **Not met** |
| Susceptibility | Flood-in-high class | > 60% | 67.1% | **Met** |

Objective (i) was met, with the two source substitutions documented in Table 4.1. Objective (ii) was met in full. Objective (iii) was met in construction but **not** in validation. Objective (iv) was met functionally but not architecturally. Objective (v) is therefore **partially** met: the SWAT criterion is satisfied, the susceptibility criteria are not.

P-factor and R-factor were not computed because calibration was performed through direct parameter manipulation rather than SWAT-CUP/SUFI-2, and no uncertainty ensemble was generated. This is recorded in Section 5.4.

## **4.9 Discussion**

### **4.9.1 A Model That Ranks Well but Discriminates Weakly**

The central finding of the spatial validation is the contrast between Table 4.11 and Table 4.12. Enrichment rises monotonically across all five zones, yet AUC-ROC reaches only 0.62 and specificity barely exceeds chance. These results are consistent rather than contradictory: the map carries genuine information about *relative* susceptibility while lacking the sharpness to classify individual locations.

For the intended decision-support purpose this distinction matters. A planner asking which parts of Lagos warrant priority attention is served by a map that ranks correctly. A planner asking whether a specific parcel will flood is not. The portal's framing as a susceptibility and scenario tool rather than a predictive instrument is therefore consistent with what the validation demonstrates.

### **4.9.2 Calibration Against a Modelled Reference**

Because GEOGLOWS is itself a model output, the statistics in Table 4.2 measure agreement between two models rather than agreement with observation. This is a recognised approach in ungauged and poorly gauged basins and was adopted deliberately, but it constrains the strength of any claim made from it.

The independent evapotranspiration check in Section 4.4 partially offsets this constraint by introducing a variable and a data source unconnected to GEOGLOWS, one of which (MODIS) is a direct satellite retrieval. That the model reproduces annual ET volume to within 14.4% without ever having been fitted to ET provides evidence of physical realism that the discharge statistics alone cannot supply. The corresponding failure to reproduce seasonal ET amplitude is equally informative and is the model's clearest identified weakness.

### **4.9.3 Terrain Weighting and Urban Pluvial Flooding**

Section 4.6.4 raises the possibility that the susceptibility map systematically under-represents flooding in dense inland LGAs. The AHP weighting offers a plausible mechanism: elevation, TWI, distance to rivers, flow accumulation and slope together account for 0.75 of the index, all of which describe *terrain position*. Flooding caused by insufficient or obstructed drainage in built-up areas is largely independent of terrain position at the 30 m scale and is represented only through the land-use factor, which carries a weight of 0.05 and derives from a classification with approximately 53% accuracy.

Two independent observations are consistent with this interpretation: the negative rank correlation in Table 4.13, and the low modelled exposure of Alimosho, Agege and Ifako/Ijaye despite their high reported flood incidence. Neither observation is conclusive, since both derive from a dataset confounded by population. The hypothesis is offered as the most productive direction for further work rather than as an established result, and Section 5.6 sets out how it could be tested.

### **4.9.4 Comparison with Published Susceptibility Studies**

The AUC of 0.62 obtained here is lower than values commonly reported in the flood susceptibility literature, where AUC above 0.80 is frequently achieved. Three differences in validation design are relevant to that comparison.

First, many published studies validate against inventories of flood *points* that were themselves used, in whole or in part, to inform factor weighting, which inflates apparent performance. The present validation used an entirely independent satellite-derived flood extent that played no role in constructing the map.

Second, validating against a continuous 35.2 km² flood extent is a substantially more demanding test than validating against a small set of discrete points, since it requires the model to discriminate across every cell of the observed footprint.

Third, AHP weights here were assigned from expert judgement without calibration against observed flooding, whereas data-driven approaches such as random forest or logistic regression fit weights to the inventory directly and would be expected to score higher on it.

The lower AUC therefore reflects a stricter validation design as well as genuine model limitations, and the two contributions cannot be separated from the present results alone. Section 5.6 recommends the comparison that would separate them.

---

# **CHAPTER FIVE**

# **CONCLUSIONS AND RECOMMENDATIONS**

## **5.1 Summary of the Study**

This study set out to build an interactive web GIS portal for flood risk analysis in Lagos State, supported by SWAT+ hydrological simulation and AHP-based susceptibility mapping, and to validate both components against defined acceptance criteria.

A harmonised geospatial data stack was assembled at 30 m resolution in EPSG:32631. A SWAT+ model of the 19,915 km² Ogun catchment was constructed, calibrated and validated against GEOGLOWS monthly discharge, and run under baseline, extreme historical and climate-sensitivity scenarios. A flood susceptibility map was produced by AHP-weighted overlay of eight conditioning factors and combined with WorldPop population data to quantify exposure. Both model components were then subjected to independent validation: the hydrological model against satellite evapotranspiration, and the susceptibility map against observed flood extent and agency flood records. All outputs were served through an interactive portal.

## **5.2 Conclusions**

**5.2.1** A SWAT+ model of the Ogun catchment calibrated against modelled discharge achieves satisfactory monthly performance by the criteria of Moriasi *et al.* (2007), with full-period NSE 0.507, R² 0.606 and PBIAS +1.6%. Validation-period performance exceeds calibration-period performance, indicating the parameter set is not over-fitted. The margins above threshold are nonetheless narrow and the model should be regarded as satisfactory rather than robust.

**5.2.2** Catchment discharge response to increased rainfall is **non-linear**: a 10% rainfall increase produces a 15.5% increase in mean discharge and a 30% increase produces 47.6%. Linear scaling of rainfall inputs therefore understates the hydrological consequences of intensifying rainfall, which supports the inclusion of a process-based component alongside index-based mapping.

**5.2.3** Independent validation against two unrelated evapotranspiration products, one of them a direct satellite retrieval, shows that the model reproduces annual evapotranspiration volume to within 14.4% while underestimating its seasonal amplitude by approximately a factor of three. Because the model was never calibrated to evapotranspiration, this constitutes genuine out-of-sample evidence of partial physical realism together with a specific, identified deficiency.

**5.2.4** Improving simulated evapotranspiration and maintaining discharge performance are **mutually incompatible** within the available parameter space. The PET multiplier is constrained at its permitted maximum, and relaxing it improves evapotranspiration while driving discharge performance below the study's acceptance thresholds.

**5.2.5** The AHP susceptibility map **ranks** flood susceptibility correctly: observed flooding is enriched monotonically across the five zones, reaching 1.61 times chance expectation in the Very High zone, and 67.1% of observed flood extent falls in the High and Very High zones against 48.9% of the state area.

**5.2.6** The same map **fails three of the four acceptance criteria** set for it. AUC-ROC of 0.62 falls below the 0.70 threshold; sensitivity of 0.685 falls below 0.70; overall accuracy of 0.526 falls well below 0.70. Only the flood-in-high-class criterion of 60% is satisfied. The map possesses ordinal but not classificatory skill, and Objective (v) is consequently only partially attained.

**5.2.7** An estimated **4,810,069 residents, or 38.7% of the population of Lagos State, occupy High or Very High susceptibility zones**, with LGA-level exposure ranging from 67.8% in Eti-Osa to 7.2% in Ifako/Ijaye. This estimate is conditional on the susceptibility classification whose limitations are stated in 5.2.6.

**5.2.8** Agency flood-report counts are unsuitable as a validation dataset for susceptibility mapping in this setting. NEMA 2022 records correlate more strongly with raw population (ρ = +0.57) than with modelled exposure (ρ = +0.17), indicating that they principally record reporting effort. This is a methodological finding of value to subsequent studies contemplating the same data source.

**5.2.9** A functional decision-support portal integrating hazard, exposure, scenario and validation views can be delivered on a lightweight single-process architecture, without the spatial database and tile-server stack originally specified.

## **5.3 Contributions of the Study**

The study makes four contributions.

It provides the first calibrated SWAT+ model of the Ogun catchment, to the author's knowledge, that is validated by a documented multi-variable strategy in the absence of gauged discharge, together with a complete and reproducible build record.

It demonstrates a validation design for AHP susceptibility mapping that uses an entirely independent satellite-derived flood extent rather than an inventory implicated in the weighting, and reports the resulting statistics without adjustment.

It documents, with quantified evidence, that agency flood-report counts are confounded by population and reporting effort, and should not be used uncritically as susceptibility validation data in Nigerian contexts.

It delivers an operational portal that makes hazard, exposure, scenario and validation results directly accessible to non-specialist users, with the limitations of each component visible within the interface rather than confined to documentation.

## **5.4 Limitations of the Study**

**Discharge reference.** No gauged discharge was obtained. Calibration and validation used GEOGLOWS modelled discharge, so the statistics of Table 4.2 measure inter-model agreement rather than agreement with observation.

**Uncertainty analysis.** P-factor and R-factor were not computed. Calibration was performed by direct parameter manipulation rather than SUFI-2/SWAT-CUP, and no uncertainty ensemble exists. Two acceptance criteria of Table 3.6 therefore remain unassessed.

**Reservoir operation.** Oyan Dam lies within the modelled basin and its releases are not represented. The 2022 flood, which was substantially release-driven, is consequently outside the model's representational scope.

**Soil representation.** Soils were represented by a single topsoil texture layer derived from SoilGrids 0–5 cm, with 88% of the basin assigned to one texture class. Vertical soil structure is not represented.

**Flood inventory resolution.** The 2012 MODIS extent has a resolution of 250 m, which cannot resolve street-scale urban flooding. Non-detection is not evidence of no flooding, and validation statistics are conditional on what MODIS can observe.

**Single validation event.** The susceptibility map is a static surface validated against one flood season. Its performance under other events is unknown.

**LULC accuracy.** The land-cover input has approximately 53% classification accuracy, limiting the reliability of the factor that would otherwise capture urban surface conditions.

**Portal architecture.** The delivered stack departs from the specification in Objective (iv), as recorded in Section 4.7.

**Evapotranspiration seasonality.** The model's simulated ET seasonal amplitude is approximately three times too flat, as established in Section 4.4.2.

## **5.5 Recommendations**

**5.5.1 For the reporting of this study.** The acceptance criteria in Section 1.3 and Section 3.8.2 are internally inconsistent, stating AUC ≥ 0.75 and AUC > 0.70 respectively. This should be reconciled before submission. Objective (iv) should be reworded to describe the delivered architecture, or the specified stack implemented. The susceptibility validation outcome should be reported as obtained; the shortfall against threshold is a defensible result given the strictness of the validation design set out in Section 4.9.4.

**5.5.2 For operational use.** The susceptibility map should be used for **relative prioritisation** between areas and not for site-specific determinations. The portal's existing framing as a susceptibility and scenario tool rather than a forecast should be preserved in any published version.

**5.5.3 For LASEMA and allied agencies.** Flood incident reporting should record **coordinates**, not community names alone. The principal obstacle to validating flood models for Lagos is the absence of a geolocated flood inventory, and Section 4.6.4 quantifies the consequence: an otherwise valuable 62-record dataset could support only LGA-level analysis, which proved confounded by population.

**5.5.4 For water resources management.** The non-linear discharge response quantified in Table 4.4 should inform drainage and reservoir planning. A 30% rainfall increase produces a 47.6% increase in mean discharge and a 28.2% increase in peak-month discharge at the Ogun outlet.

## **5.6 Recommendations for Further Research**

**5.6.1 Test the terrain-weighting hypothesis.** The proposition advanced in Section 4.9.3 — that the index under-represents urban pluvial flooding — is testable. Re-running the overlay with the susceptibility surface stratified by built-up density would establish whether enrichment falls systematically in dense urban LGAs. If confirmed, a drainage-related factor such as impervious fraction or drainage density should enter the index at a materially higher weight than the 0.05 currently assigned to land cover.

**5.6.2 Benchmark against a data-driven model.** Fitting logistic regression or random forest models to the same conditioning factors and the same 2012 flood extent would separate the contribution of AHP's uncalibrated weighting from the strictness of the validation design, resolving the ambiguity identified in Section 4.9.4.

**5.6.3 Complete the uncertainty analysis.** Running SUFI-2 over the calibrated parameter set would produce the P-factor and R-factor left unassessed in Table 4.14 and place confidence bounds on the scenario results of Table 4.4.

**5.6.4 Represent Oyan Dam.** Incorporating reservoir operation would bring the 2022 event within the model's scope and materially improve its value for flood early warning, since release-driven events are precisely those for which advance notice is achievable.

**5.6.5 Extend the flood inventory.** Sentinel-1 SAR offers 10 m all-weather flood mapping, an order of magnitude finer than the 250 m MODIS product used here, and would permit validation at a scale appropriate to urban flooding. Compiling extents for several flood seasons would also replace the single-event validation with a multi-event assessment.

**5.6.6 Resolve the evapotranspiration deficiency.** The seasonal amplitude problem identified in Section 4.4.2 warrants investigation of whether it originates in the CHIRPS rainfall forcing, the single-layer soil representation, or the PET formulation. Multi-variable calibration with ET and discharge weighted jointly, using a widened `petco` range, would establish whether an acceptable compromise exists.

## **5.7 Concluding Remark**

The study delivers a calibrated hydrological model that meets its performance criteria, a susceptibility map that ranks flood-prone areas correctly but does not meet its discriminatory thresholds, and a working portal that makes both accessible together with their limitations. The mixed outcome is reported deliberately. A validation exercise that confirmed every expectation would provide weaker evidence of rigour than one that identified where the models succeed, where they fall short, and by how much.
