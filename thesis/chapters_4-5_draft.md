CHAPTER FOUR

RESULTS AND ANALYSIS

**4.1 Introduction**

This chapter presents the results obtained from the hydrological modelling, flood susceptibility mapping, and validation procedures described in Chapter Three. The results are analysed and compared against the acceptance criteria defined in Table 3.6 to evaluate whether each component of the study meets the performance standards set for it. The chapter is organized to present the assembled data stack, the SWAT+ model setup and calibration results, scenario simulation results, independent evapotranspiration validation, flood susceptibility and exposure results, spatial validation of the susceptibility map, the developed web portal, and a summary of attainment against all acceptance criteria.

**4.2 Data Acquisition and Preprocessing Results**

Below are the results of the data acquisition and harmonisation procedures carried out before modelling;

**4.2.1 Final Assembled Data Stack**

Table 4.1 Final data stack and deviations from proposed sources

| Layer | Source used | Resolution | Deviation from Section 3.3 |
|---|---|---|---|
| Rainfall (SWAT forcing) | CHIRPS daily | 5 km, 23 stations | None |
| Temperature | ERA5-Land tmax/tmin | 9 km | None |
| Rainfall (statistics) | NiMet Ikeja, 1996–2025 | Station | None |
| DEM | Copernicus GLO-30 | 30 m → 90 m | SRTM replaced |
| Rivers and basins | HydroRIVERS v1.0 | Vector | None |
| Land cover | ESA WorldCover v200 | 10 m → 90 m | None |
| Soil | SoilGrids 0–5 cm sand/clay | 250 m → 90 m | Single layer only |
| Discharge | GEOGLOWS v2, reach 140585128 | Daily, 1940–2026 | NIHSA replaced |
| Flood inventory | MODIS 2012 extent; NEMA 2022 | 250 m / LGA | Compiled from open archives |
| Population | WorldPop | 100 m | None |

From the results in Table 4.1 above, all ten layers required for the study were successfully acquired, reprojected to EPSG:32631, and clipped to their respective study extents with no gaps in coverage. The success criterion stated in Objective (i) is therefore satisfied.

Two of the ten layers were obtained from sources other than those originally proposed. The Shuttle Radar Topography Mission DEM was replaced with the Copernicus GLO-30 DEM because the available SRTM tiles terminated at 7°N and did not cover the northern headwaters of the Ogun basin, which extend to approximately 8.95°N. The Copernicus product offers equivalent 30 m resolution with complete basin coverage.

Observed discharge from the Nigeria Hydrological Services Agency was not obtained within the project period. GEOGLOWS ECMWF retrospective discharge at reach 140585128, located at Kara/Akute on the Ogun main stem, was adopted in its place. This series comprises 31,589 daily values covering 1940 to 2026, aggregated to monthly means for model evaluation.

**4.3 SWAT+ Model Setup Results**

**4.3.1 Catchment Delineation**

Table 4.2 Catchment delineation results

| Property | Value |
|---|---|
| Delineated catchment area | 19,915 km² |
| Number of subbasins | 23 |
| Number of channels | 71 |
| Number of landscape units | 71 |
| Number of HRUs | 243 (from 1,971 candidates) |
| Outlet location | Kara/Akute, UTM 31N 542139 E, 736226 N |
| HydroRIVERS reference area | 24,816 km² |

The results in Table 4.2 above show a delineated catchment area of 19,915 km², which compares with an independent HydroRIVERS upstream-area estimate of 24,816 km² for the Ogun basin as a whole. The delineated extent therefore represents the portion of the Ogun system draining to the Kara/Akute outlet above the Lagos Lagoon.

An initial delineation performed without stream burn-in produced a maximum flow accumulation of only 462 km², approximately 2% of the expected catchment area. Inspection confirmed the DEM contained no voids and had a valid elevation range of 0 to 585 m, indicating that the failure arose from flow dispersion across the flat valley terrain rather than from data gaps. Burning in the HydroRIVERS network and relocating the outlet to the nearest main-stem vertex raised maximum flow accumulation to 20,592 km², producing the delineation reported above.

**4.3.2 HRU Input Characteristics**

Table 4.3 Basin land cover and soil composition

| Land cover class | % of basin | Soil texture | % of basin |
|---|---|---|---|
| Tree cover | 43.0 | Sandy loam | 88.0 |
| Shrubland | 23.0 | Sandy clay loam | 11.0 |
| Cropland | 16.0 | Other | 1.0 |
| Grassland | 12.0 | | |
| Built-up | 4.5 | | |

From the results in Table 4.3 above, the basin is predominantly vegetated, with tree cover and shrubland together accounting for 66% of the area and built-up surfaces occupying only 4.5%. Soils are dominated by two textures, with sandy loam covering 88% of the basin. The low variability in soil texture permitted representation through a custom user-soil database containing twelve texture classes built on the FAO schema.

**4.4 SWAT+ Calibration and Validation Results**

**4.4.1 Baseline Uncalibrated Performance**

Table 4.4 Uncalibrated model performance against GEOGLOWS monthly discharge, 2011–2023

| Metric | Value | Criterion (Table 3.6) | Status |
|---|---|---|---|
| NSE | −0.10 | > 0.50 | Not met |
| R² | 0.51 | > 0.60 | Not met |
| PBIAS | −48.9% | < ±25% | Not met |
| Mean simulated | 337 m³/s | — | — |
| Mean observed | 226 m³/s | — | — |

The results in Table 4.4 above show that the uncalibrated model failed all three acceptance criteria. The combination of a moderate R² of 0.51 with a strongly negative NSE indicates that the model reproduced the seasonal shape of the hydrograph while partitioning water incorrectly. Simulated wet-season peaks were substantially overestimated, while dry-season baseflow was severely underestimated, with simulated January to March flows of approximately 4 m³/s against observed values near 50 m³/s. Calibration was therefore required before the model could be used for scenario analysis.

**4.4.2 Calibrated Parameter Set**

Table 4.5 Final calibrated parameter values

| Parameter | Description | Value | Permitted range |
|---|---|---|---|
| perco | Percolation coefficient | 0.30 | 0.00–1.00 |
| petco | PET multiplier | 1.20 | 0.80–1.20 |
| canmx | Maximum canopy storage (mm) | 12.0 | 0.00–100.0 |
| alpha | Baseflow alpha factor | 0.022 | 0.00–1.00 |
| flo_min | Minimum aquifer storage for return flow (mm) | 10.0 | — |
| bf_max | Maximum baseflow rate | 0.55 | — |

From the results in Table 4.5 above, six parameters were adjusted from their defaults. Reducing the percolation coefficient from its default of 0.90 to 0.30 produced the first substantial improvement, raising NSE from −0.10 to 0.18, and identified the catchment as baseflow-dominated with surface runoff contributing approximately 18 mm/yr. Raising the PET multiplier to 1.20 moved PBIAS from −30% to +3%. Canopy storage of 12 mm reduced excessive wet-season peaks, and the three aquifer parameters restored dry-season baseflow.

It is noted that petco reached 1.20, which is the maximum value permitted by the SWAT+ parameter database. The implications of this constraint are examined in Section 4.6.3.

The soil evaporation compensation factor, plant uptake compensation factor and available water capacity were tested during calibration and were found to be either inert or to move the simulation in the wrong direction in this SWAT+ revision. They were therefore excluded from the final parameter set.

**4.4.3 Calibrated Model Performance**

Table 4.6 Calibrated SWAT+ performance against GEOGLOWS monthly discharge

| Period | NSE | R² | PBIAS | Criterion | Status |
|---|---|---|---|---|---|
| Calibration, 2011–2017 | 0.41 | 0.56 | +6.1% | NSE > 0.50, R² > 0.60, PBIAS < ±25% | Partially met |
| Validation, 2018–2023 | 0.57 | 0.64 | −3.2% | NSE > 0.50, R² > 0.60, PBIAS < ±25% | Met |
| Full period, 2011–2023 | 0.507 | 0.606 | +1.6% | NSE > 0.50, R² > 0.60, PBIAS < ±25% | Met |

The results in Table 4.6 above show that the calibrated model satisfies all three acceptance criteria over the full evaluation period, with NSE of 0.507, R² of 0.606 and PBIAS of +1.6%. Objective (ii) is therefore met. Mean simulated discharge of 222 m³/s compares with 226 m³/s observed.

Validation-period performance exceeds calibration-period performance on all three metrics. This indicates that the parameter set is not over-fitted to the calibration window.

It is further noted that the full-period margins above threshold are narrow. NSE exceeds its criterion by 0.007 and R² by 0.006. The model is therefore satisfactory but only marginally so, and any subsequent change to forcing data or parameter values would require the evaluation to be repeated.

**4.4.4 Monthly Hydrograph Comparison**

Table 4.7 Observed and simulated monthly discharge climatology (m³/s), 2011–2023

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Observed | 69 | 47 | 42 | 59 | 90 | 184 | 328 | 332 | 684 | 518 | 235 | 116 |
| Simulated | 44 | 26 | 14 | 13 | 23 | 115 | 312 | 363 | 760 | 720 | 196 | 72 |

From the results in Table 4.7 above, the model reproduces the timing of the flood season, including the September maximum that drives fluvial discharge into the Lagos Lagoon. Two discrepancies are evident. October discharge is overestimated at 720 m³/s against 518 m³/s observed, indicating that recession from the wet season is too slow. The February to May transition remains underestimated, indicating that the early rains generate insufficient flow in the simulation.

**4.5 Scenario Simulation Results**

Table 4.8 Simulated outlet discharge under rainfall scenarios

| Scenario | Mean (m³/s) | Change in mean | Peak month (m³/s) | Change in peak |
|---|---|---|---|---|
| Baseline | 222 | — | 1420 | — |
| +10% rainfall | 257 | +15.5% | 1558 | +9.7% |
| +20% rainfall | 292 | +31.3% | 1686 | +18.7% |
| +30% rainfall | 328 | +47.6% | 1821 | +28.2% |

The results in Table 4.8 above show that catchment discharge responds non-linearly to increased rainfall. A 10% increase in rainfall produces a 15.5% increase in mean discharge, and a 30% increase produces a 47.6% increase. The amplification factor is therefore approximately 1.55 across the range tested.

Peak-month discharge responds less strongly than mean discharge, rising by 28.2% under a 30% rainfall increase. This indicates that the additional rainfall volume is distributed across the wet season rather than concentrated at the seasonal maximum.

Table 4.9 Extreme historical scenario results

| Scenario | Annual mean (m³/s) | Peak month (m³/s) |
|---|---|---|
| Wettest simulated year (2019) | 308 | 1053 |
| 2022 flood year | Near baseline | Near baseline |

From the results in Table 4.9 above, the wettest year in the simulation period was 2019, producing an annual mean of 308 m³/s. The 2022 flood year, which produced severe flooding nationally, returned near-baseline discharge in the rainfall-only simulation. This is consistent with documented evidence that the 2022 event in this basin was driven substantially by releases from Oyan Dam rather than by rainfall alone. As reservoir operation is not represented in the model, the 2022 event falls outside its representational scope.

The three scenario families required by Objective (ii), comprising baseline, extreme historical and climate sensitivity, were therefore produced.

**4.6 Independent Evapotranspiration Validation Results**

**4.6.1 Basis of the Validation**

The calibration reported in Section 4.4 used GEOGLOWS discharge for both the calibration and validation periods, separated only in time. To provide a test independent of that data source, simulated evapotranspiration was compared against two unrelated reference products. Evapotranspiration entered no part of the calibration objective function, so agreement constitutes an out-of-sample test rather than a fitted result.

**4.6.2 Comparison Against Reference Products**

Table 4.10 Simulated evapotranspiration against independent references, 155 months

| Reference | NSE | R² | PBIAS | Criterion | Status |
|---|---|---|---|---|---|
| MODIS MOD16A2GF | 0.14 | 0.36 | +14.4% | PBIAS < ±25% | Met |
| TerraClimate AET | 0.18 | 0.39 | +12.5% | PBIAS < ±25% | Met |

Table 4.11 Annual evapotranspiration totals

| Source | Annual mean (mm/yr) |
|---|---|
| MODIS MOD16A2GF | 920 |
| TerraClimate AET | 900 |
| SWAT+ simulated | 787 |

The results in Tables 4.10 and 4.11 above show that annual evapotranspiration volume falls within the ±25% acceptance band against both references, at +14.4% and +12.5% respectively. Monthly agreement is weak, with NSE of 0.14 and 0.18.

The two reference products agree with each other to within 20 mm/yr, or approximately 2%, despite being derived by entirely different methods. MODIS MOD16A2GF is a satellite retrieval, while TerraClimate is a climatic water-balance product. Their agreement indicates that the discrepancy with the simulation is a property of the model rather than an artefact of a single reference dataset.

Table 4.12 Monthly evapotranspiration climatology (mm), MODIS against simulated

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MODIS | 27.8 | 32.1 | 53.7 | 65.0 | 87.0 | 101.7 | 110.2 | 112.3 | 113.6 | 88.5 | 83.2 | 41.9 |
| Simulated | 55.9 | 49.8 | 59.5 | 64.9 | 75.6 | 68.8 | 67.9 | 65.4 | 70.7 | 73.8 | 72.0 | 63.0 |

From the results in Table 4.12 above, MODIS evapotranspiration varies across an annual range of approximately 86 mm, while the simulated series varies across approximately 26 mm. The simulated seasonal amplitude is therefore approximately one third of that observed. The model produces excess evapotranspiration during the dry season and a deficit at the wet-season maximum, while returning approximately the correct annual total.

**4.6.3 Multi-Variable Calibration Test**

Table 4.13 Simultaneous discharge and evapotranspiration performance

| petco | Discharge NSE | Discharge R² | Discharge PBIAS | ET NSE | ET PBIAS | Meets Table 3.6 |
|---|---|---|---|---|---|---|
| 1.20 (adopted) | 0.507 | 0.606 | +1.6% | 0.14 | +14.4% | Yes |
| 1.35 | 0.530 | 0.596 | +15.7% | 0.30 | +6.6% | No |
| 1.50 | 0.507 | 0.583 | +28.7% | 0.37 | +1.1% | No |

The results in Table 4.13 above show that evapotranspiration performance improves monotonically as the PET multiplier is raised, with ET NSE rising from 0.14 to 0.37, while discharge performance falls below the acceptance criteria. At petco of 1.35 the discharge R² of 0.596 falls below the criterion of 0.60. At petco of 1.50 both R² and PBIAS fail.

The two objectives are therefore in direct conflict within the available parameter space, and the adopted parameter set of petco 1.20 is the only value tested that satisfies the discharge criteria. It was retained on that basis. Values of 1.35 and 1.50 were reachable only by temporarily raising the permitted parameter ceiling, which was restored afterwards.

**4.7 Flood Susceptibility Mapping Results**

**4.7.1 Pairwise Comparison Matrix and Consistency Check**

Table 4.14 Pairwise comparison matrix for the eight susceptibility factors

| Factor | Elev | TWI | DistRiv | FlowAcc | Runoff | Slope | Rain | LULC |
|---|---|---|---|---|---|---|---|---|
| Elevation | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 4 |
| TWI | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 4 |
| Distance to rivers | 1 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |
| Flow accumulation | 1/2 | 1/2 | 1 | 1 | 1 | 1 | 2 | 2 |
| Runoff | 1/2 | 1/2 | 1 | 1 | 1 | 1 | 2 | 2 |
| Slope | 1/2 | 1/2 | 1/2 | 1 | 1 | 1 | 1 | 2 |
| Extreme rainfall | 1/3 | 1/2 | 1/2 | 1/2 | 1/2 | 1 | 1 | 2 |
| Land use / land cover | 1/4 | 1/4 | 1/3 | 1/2 | 1/2 | 1/2 | 1/2 | 1 |

*[Editorial note, to be removed before submission: verify that every judgement in Table 4.14 reflects your own reasoning about Lagos flood processes. The matrix reproduces the weights actually applied in the model, but the judgements must be yours to defend. Adjust any entry you disagree with and re-run `validation/ahp_consistency.py` to obtain the revised weights and CR.]*

Table 4.15 Derived AHP weights, applied weights, and consistency statistics

| Factor | Derived weight | Applied weight | Difference |
|---|---|---|---|
| Elevation | 0.202 | 0.20 | +0.002 |
| Topographic Wetness Index | 0.192 | 0.18 | +0.012 |
| Distance to rivers | 0.156 | 0.15 | +0.006 |
| Flow accumulation | 0.114 | 0.12 | −0.006 |
| Runoff (SCS-CN) | 0.114 | 0.12 | −0.006 |
| Slope | 0.096 | 0.10 | −0.004 |
| Extreme rainfall | 0.077 | 0.08 | −0.003 |
| Land use and land cover | 0.050 | 0.05 | 0.000 |
| **Total** | **1.000** | **1.00** | — |

| Consistency statistic | Value | Criterion | Status |
|---|---|---|---|
| λ_max | 8.1139 | — | — |
| Consistency Index (CI) | 0.0163 | — | — |
| Random Index (RI), n = 8 | 1.41 | — | — |
| **Consistency Ratio (CR)** | **0.0115** | **≤ 0.10** | **Met** |

The results in Tables 4.14 and 4.15 above show a Consistency Ratio of 0.0115, which is well below the acceptance criterion of 0.10 stated in Section 3.6.3. The pairwise judgements are therefore sufficiently coherent, and the derived weight vector is accepted. Weights were obtained by the geometric mean approximation to the principal eigenvector, as specified in Section 3.6.3, and λ_max was computed from the resulting weight vector.

The weights applied in the model were rounded to two decimal places, as recorded in the model configuration. The maximum difference between the derived and applied values is 0.012, occurring for the Topographic Wetness Index, and arises because pairwise judgements are restricted to Saaty's integer scale and its reciprocals. A difference of this magnitude is immaterial to the classification, since the susceptibility index is subsequently divided into five equal-interval classes.

From the results in Table 4.15 above, the weighting is dominated by terrain variables. Elevation and the Topographic Wetness Index together account for 0.394 of the index, and the five terrain-related factors, comprising elevation, TWI, distance to rivers, flow accumulation and slope, together account for 0.760. The two rainfall-driven components, runoff and extreme rainfall, account for 0.191, and land use and land cover for 0.050.

The implications of this distribution for the map's ability to represent flooding that is not controlled by terrain position are examined in Section 5.1.

**4.7.2 Susceptibility Classification and Population Exposure**

Table 4.16 Susceptibility zone areas and resident population, Lagos State

| Zone | Area (km²) | % of Lagos | Population | % of population |
|---|---|---|---|---|
| Very Low | 0.8 | 0.02 | 10,077 | 0.08 |
| Low | 168.7 | 4.46 | 692,475 | 5.58 |
| Moderate | 1,762.9 | 46.61 | 6,908,435 | 55.62 |
| High | 1,055.9 | 27.92 | 4,368,569 | 35.17 |
| Very High | 793.7 | 20.99 | 441,500 | 3.55 |
| **Total** | **3,781.9** | **100.00** | **12,421,056** | **100.00** |

Areas in Table 4.16 are computed over the twenty Local Government Area boundaries of Lagos State, and the column total of 3,781.9 km² corresponds to the area of the LGA boundary polygon. Zone areas computed over the full raster extent are larger, since the hazard grid extends beyond the state boundary across the lagoon and into adjoining territory; those figures do not describe Lagos State and are not reported here.

The results in Table 4.16 above show that 4,810,069 residents, representing 38.7% of the state population, fall within the High or Very High susceptibility zones. The High and Very High zones together cover 1,849.6 km², or 48.91% of the state area.

Table 4.17 Highest and lowest LGA exposure

| LGA | % population in High or Very High |
|---|---|
| Eti-Osa | 67.8 |
| Lagos Island | 65.0 |
| Shomolu | 58.2 |
| Ojo | 53.4 |
| Ikeja | 10.9 |
| Agege | 9.9 |
| Ifako/Ijaye | 7.2 |

From the results in Table 4.17 above, exposure ranges from 67.8% in Eti-Osa to 7.2% in Ifako/Ijaye. The highest-exposure LGAs lie along the coastal and lagoon-adjacent low-lying belt, which is consistent with the terrain-dominated weighting reported in Table 4.14.

**4.7.3 Rainfall Frequency Analysis**

Table 4.18 Gumbel design rainfall, NiMet Ikeja station, 1996–2025

| Return period (years) | 2 | 5 | 10 | 25 | 50 | 100 |
|---|---|---|---|---|---|---|
| Design rainfall (mm) | 1,734 | 2,205 | 2,516 | 2,909 | 3,201 | 3,490 |

The results in Table 4.18 above were derived from a Gumbel distribution fitted to the annual series with location parameter 1582.4 and scale parameter 414.8. Mean annual rainfall over the record is 1,821.8 mm.

The observed maximum of 3,931.7 mm, recorded in 2018, corresponds to a return period of approximately 289 years on this fit. This indicates either an exceptional event or that the Gumbel distribution understates the upper tail at this station.

Mann-Kendall testing found no significant trend in annual rainfall over the record, with Z of 0.18 and p of 0.86. A significant increasing trend was found in mean annual temperature, with Z of 4.17, p below 0.001, and a slope of +0.44 °C per decade.

**4.8 Spatial Validation Results**

**4.8.1 Validation Datasets**

Two independent observational datasets were compiled from open archives, as no comprehensive spatial flood database exists for Lagos State.

Table 4.19 Flood validation datasets

| Dataset | Source | Coverage in Lagos |
|---|---|---|
| MODIS 250 m flood extent, Jul–Nov 2012 | NASA/DFO via HDX | 35.2 km² across 290 patches |
| NEMA 2022 flood records | NEMA via HDX | 62 reports across 13 of 20 LGAs |

From the results in Table 4.19 above, the 2012 MODIS product provides 35.2 km² of detected flood extent within Lagos State, distributed across 290 discrete patches. Permanent water bodies are masked in the source product, so the extent represents detected flooding rather than the lagoon system.

No geocoding of NEMA community names was attempted. The records carry community names but no coordinates, and assigning coordinates from place names would introduce fabricated locations into the dataset used for validation. The NEMA records were therefore analysed only at the LGA level of aggregation that the source supports.

**4.8.2 Overlay Analysis**

Table 4.20 Distribution of observed 2012 flood extent across susceptibility zones

| Zone | % of observed flood | % of Lagos area | Enrichment ratio |
|---|---|---|---|
| Very Low | 0.00 | 0.02 | 0.00 |
| Low | 2.32 | 4.46 | 0.52 |
| Moderate | 30.61 | 46.61 | 0.66 |
| High | 33.19 | 27.92 | 1.19 |
| Very High | 33.89 | 20.99 | 1.61 |
| High + Very High | 67.08 | 48.91 | 1.37 |

The results in Table 4.20 above show that the enrichment ratio, calculated as the share of observed flooding in a zone divided by that zone's share of the state area, rises monotonically across the five susceptibility classes. Observed flooding is 1.61 times more concentrated in the Very High zone than would occur by chance, and is depleted in the Low and Moderate zones at ratios of 0.52 and 0.66 respectively.

The proportion of observed flooding falling in the High and Very High classes is 67.08%, against the acceptance criterion of greater than 60% stated in Table 3.6. This criterion is met.

It is noted that the High and Very High zones together cover 48.91% of the state. A randomly assigned classification would therefore place approximately 49% of observed flooding within them, and the measured 67.08% represents an improvement of 18 percentage points over chance.

**4.8.3 Discriminatory Power and Confusion Matrix**

Table 4.21 Susceptibility map discriminatory performance

| Metric | Value | Criterion (Table 3.6) | Status |
|---|---|---|---|
| AUC-ROC | 0.62 | > 0.70 | Not met |
| Sensitivity | 0.685 | ≥ 0.70 | Not met |
| Specificity | 0.494 | — | — |
| Overall accuracy | 0.526 | > 0.70 | Not met |
| Precision | 0.213 | — | — |
| Flood-in-high class | 67.08% | > 60% | Met |

Table 4.22 Confusion matrix at the Youden-optimal threshold, FSI = 0.596

| | Predicted flood | Predicted non-flood |
|---|---|---|
| Observed flood | 26,799 | 12,309 |
| Observed non-flood | 98,888 | 96,652 |

The results in Tables 4.21 and 4.21 above show that the susceptibility map meets one of the four acceptance criteria set for it. The AUC-ROC of 0.62 falls below the criterion of 0.70, though it exceeds 0.50, which would indicate no discrimination. Sensitivity of 0.685 falls marginally below the criterion of 0.70, and overall accuracy of 0.526 falls substantially below it.

Specificity of 0.494 and precision of 0.213 identify the cause. Because the High and Very High zones occupy 48.91% of the state, they capture flooded and non-flooded ground at approximately the same rate. Of 125,687 cells predicted as flood-prone at the optimal threshold, 98,888 were not flooded in the 2012 event.

Objective (v) is therefore only partially attained. The SWAT criterion is satisfied, while the susceptibility criteria are not.

**4.8.4 LGA-Level Comparison with NEMA Records**

Table 4.23 Spearman rank correlation between NEMA report counts and modelled quantities

| Compared quantity | Spearman ρ |
|---|---|
| Modelled % population in High or Very High | −0.45 |
| Modelled absolute population exposed | +0.17 |
| Raw LGA population | +0.57 |

The results in Table 4.23 above show that NEMA report counts correlate more strongly with raw LGA population, at ρ of +0.57, than with either modelled exposure quantity. The Mann-Whitney comparison between LGAs with and without reports was not statistically significant, at p of 0.10.

This indicates that the NEMA dataset predominantly records where population and reporting capacity are concentrated rather than where flooding occurs. The dataset is therefore confounded and cannot validate the susceptibility map in either direction. This test is reported as inconclusive.

Table 4.24 LGAs with highest NEMA report counts against modelled exposure

| LGA | NEMA reports | Modelled % High or Very High |
|---|---|---|
| Alimosho | 11 | 14.4 |
| Ikorodu | 10 | 22.4 |
| Ojo | 10 | 53.4 |
| Epe | 7 | 23.5 |
| Kosofe | 6 | 47.1 |
| Agege | 5 | 9.9 |

From the results in Table 4.24 above, three of the six LGAs generating the most flood reports, being Alimosho, Ikorodu and Agege, rank among the lowest in modelled exposure at 14.4%, 22.4% and 9.9% respectively. These are dense inland local government areas.

**4.9 Web Portal Development Results**

Table 4.25 Delivered portal features against Objective (iv)

| Required feature | Delivered | Implementation |
|---|---|---|
| Layer control with legends | Yes | Hazard map view with five-zone legend |
| Time-series dashboard | Yes | Climate panel and SWAT+ hydrograph |
| Scenario runner | Yes | Rainfall scenario view |
| Spatial query popups | Yes | Point query view |
| Downloadable outputs | Yes | Exposure tables and scenario results |

The results in Table 4.25 above show that all five core features required by Objective (iv) were delivered. The portal provides eight views: project overview, hazard map, point query, exposure dashboard, rainfall scenario runner, climate panel, SWAT+ hydrology panel, and validation panel.

The implementation stack differs from that specified in Objective (iv). The portal was built as a Streamlit application over a single Python interface module, with Folium and Leaflet providing the interactive map. PostgreSQL/PostGIS, GeoServer, FastAPI, React and Docker were not used. The functional requirements of Objective (iv) are therefore satisfied, while the architectural specification is not.

**4.10 Summary of Attainment Against Acceptance Criteria**

Table 4.26 Attainment against the acceptance criteria of Table 3.6

| Component | Metric | Criterion | Achieved | Status |
|---|---|---|---|---|
| SWAT+ | NSE | > 0.50 | 0.507 | Met |
| SWAT+ | R² | > 0.60 | 0.606 | Met |
| SWAT+ | PBIAS | < ±25% | +1.6% | Met |
| SWAT+ | P-factor | ≥ 0.70 | Not computed | Not assessed |
| SWAT+ | R-factor | ≤ 1.5 | Not computed | Not assessed |
| Susceptibility | AUC-ROC | > 0.70 | 0.62 | Not met |
| Susceptibility | Sensitivity | ≥ 0.70 | 0.685 | Not met |
| Susceptibility | Overall accuracy | > 0.70 | 0.526 | Not met |
| Susceptibility | Flood-in-high class | > 60% | 67.08% | Met |

The results in Table 4.26 above show that four of the nine acceptance criteria were met, three were not met, and two were not assessed.

Objective (i) was met, with the two source substitutions documented in Table 4.1. Objective (ii) was met in full. Objective (iii) was met in respect of map construction but not in respect of validation performance. Objective (iv) was met functionally but not architecturally. Objective (v) was partially met.

The P-factor and R-factor criteria were not assessed because calibration was performed through direct parameter manipulation rather than through SUFI-2, and no uncertainty ensemble was generated.

CHAPTER FIVE

CONCLUSION AND RECOMMENDATION

In this chapter, the conclusions drawn from the hydrological modelling, flood susceptibility mapping and validation of both components are presented, together with recommendations for improving model performance and for the use of the outputs by stakeholders.

The primary aim of this study was to design and build an interactive web GIS portal for flood risk analysis in Lagos State, supported by SWAT+ hydrological simulation and AHP-based flood susceptibility mapping, and to validate both components against defined acceptance criteria. The research aimed to establish whether a process-based hydrological model could be calibrated for the Ogun catchment in the absence of gauged discharge, and whether the resulting susceptibility map corresponded to observed flooding.

Findings from the study show that the SWAT+ model met all three of its acceptance criteria, achieving NSE of 0.507, R² of 0.606 and PBIAS of +1.6% over the full evaluation period, with validation-period performance exceeding calibration-period performance. Catchment discharge was found to respond non-linearly to increased rainfall, with a 10% rainfall increase producing a 15.5% increase in mean discharge and a 30% increase producing 47.6%.

For the flood susceptibility map, the results were mixed. The map ranks flood susceptibility correctly, with observed flooding enriched monotonically across the five zones and reaching 1.61 times chance expectation in the Very High class. However, the map met only one of its four acceptance criteria. AUC-ROC of 0.62, sensitivity of 0.685 and overall accuracy of 0.526 all fall below their thresholds, and the map therefore possesses ordinal but not classificatory skill.

An estimated 4,810,069 residents, representing 38.7% of the population of Lagos State, were found to occupy High or Very High susceptibility zones.

**5.1 Discussion**

While the study demonstrates that a SWAT+ model can be calibrated to acceptable standards using modelled rather than gauged discharge, the results reveal two limitations that constrain the strength of the conclusions.

The first concerns the calibration reference. Because GEOGLOWS is itself a model output, the performance statistics reported in Table 4.6 measure agreement between two models rather than agreement with observation. This approach is recognised for ungauged and poorly gauged basins and was adopted deliberately following Odusanya et al. (2019), but it cannot support the same strength of claim as calibration against gauged discharge. The independent evapotranspiration validation reported in Section 4.6 partially offsets this constraint, since it introduces both a different variable and a data source unconnected to GEOGLOWS, one of which is a direct satellite retrieval. That the model reproduces annual evapotranspiration to within 14.4% without ever having been fitted to it provides evidence of physical realism that the discharge statistics alone cannot supply.

The corresponding failure to reproduce seasonal evapotranspiration amplitude, reported in Table 4.12, is the model's clearest identified weakness. The diagnosis given in Section 4.6.3 is that the PET multiplier is constrained at its permitted maximum of 1.20, while both reference products independently indicate that simulated evapotranspiration is 12 to 14% too low. Two separate lines of evidence therefore converge on the conclusion that the model requires more evapotranspiration than the parameter range permits. Relaxing that constraint improves evapotranspiration but drives discharge performance below the acceptance thresholds, so no compromise within the tested parameter space satisfies both.

The second limitation concerns the susceptibility map's discriminatory performance. The contrast between Table 4.20 and Table 4.21 is central: enrichment rises monotonically across all five zones, yet AUC-ROC reaches only 0.62 and specificity barely exceeds chance. These results are consistent rather than contradictory. The map carries genuine information about relative susceptibility while lacking the sharpness to classify individual locations, because the High and Very High zones together occupy nearly half the state.

Three differences in validation design are relevant when comparing the AUC of 0.62 obtained here with values above 0.80 commonly reported in the flood susceptibility literature. First, many published studies validate against inventories of flood points that were themselves used, in whole or in part, to inform factor weighting, which inflates apparent performance. The present validation used an independent satellite-derived flood extent that played no role in constructing the map. Second, validating against a continuous 35.2 km² flood extent is a more demanding test than validating against a small set of discrete points, as it requires discrimination across every cell of the observed footprint. Third, AHP weights were assigned from expert judgement without calibration against observed flooding, whereas data-driven approaches such as random forest or logistic regression fit weights to the inventory directly and would be expected to score higher against it. The lower AUC therefore reflects a stricter validation design as well as genuine model limitations, and these two contributions cannot be separated from the present results alone.

A further observation arises from Section 4.8.4. The AHP weighting reported in Table 4.14 assigns 0.75 of the index to terrain-related factors, all of which describe topographic position. Flooding caused by insufficient or obstructed drainage in built-up areas is largely independent of terrain position at the 30 m scale and is represented only through the land cover factor, which carries a weight of 0.05 and derives from a classification with approximately 53% accuracy. Two independent observations are consistent with this: the negative rank correlation of −0.45 in Table 4.23, and the low modelled exposure of Alimosho, Agege and Ifako/Ijaye in Table 4.24 despite their high reported flood incidence. Neither observation is conclusive, since both derive from a dataset shown to be confounded by population, but the possibility that the index systematically under-represents urban pluvial flooding warrants investigation.

Additional constraints on the study should be noted. Oyan Dam lies within the modelled basin and its releases are not represented, placing the 2022 flood outside the model's scope. Soils were represented by a single topsoil texture layer, with 88% of the basin assigned to one class. The 2012 MODIS flood extent has a resolution of 250 m, which cannot resolve street-scale urban flooding, so non-detection is not evidence of no flooding. The susceptibility map is a static surface validated against a single flood season. Finally, P-factor and R-factor were not computed, as no uncertainty ensemble was generated.

**5.2 Conclusion**

The following overall conclusions can be drawn from the results of this study:

1. A SWAT+ model of the Ogun catchment calibrated against modelled discharge achieves satisfactory monthly performance, with full-period NSE of 0.507, R² of 0.606 and PBIAS of +1.6%. Validation-period performance exceeds calibration-period performance, indicating the parameter set is not over-fitted. The margins above threshold are narrow, and the model should be regarded as satisfactory rather than robust.

2. Catchment discharge responds non-linearly to increased rainfall, with an amplification factor of approximately 1.55. Linear scaling of rainfall therefore understates the hydrological consequences of intensifying rainfall, which supports the inclusion of a process-based component alongside index-based mapping.

3. Independent validation against two unrelated evapotranspiration products, one of them a direct satellite retrieval, shows that the model reproduces annual evapotranspiration volume to within 14.4% while underestimating its seasonal amplitude by approximately a factor of three. As the model was never calibrated to evapotranspiration, this constitutes genuine out-of-sample evidence of partial physical realism together with a specific identified deficiency.

4. Improving simulated evapotranspiration and maintaining discharge performance are mutually incompatible within the available parameter space, as the PET multiplier is constrained at its permitted maximum.

5. The AHP susceptibility map ranks flood susceptibility correctly. Observed flooding is enriched monotonically across the five zones, reaching 1.61 times chance expectation in the Very High zone, and 67.08% of observed flood extent falls within the High and Very High zones against 48.91% of the state area.

6. The same map fails three of its four acceptance criteria, with AUC-ROC of 0.62, sensitivity of 0.685 and overall accuracy of 0.526. The map possesses ordinal but not classificatory skill, and Objective (v) is therefore only partially attained.

7. An estimated 4,810,069 residents, or 38.7% of the population of Lagos State, occupy High or Very High susceptibility zones, with LGA-level exposure ranging from 67.8% in Eti-Osa to 7.2% in Ifako/Ijaye. This estimate is conditional on the classification limitations stated in conclusion 6.

8. Agency flood-report counts are unsuitable as validation data for susceptibility mapping in this setting, as NEMA 2022 records correlate more strongly with raw population, at ρ of +0.57, than with modelled exposure, at ρ of +0.17.

9. A functional decision-support portal integrating hazard, exposure, scenario and validation views can be delivered on a lightweight single-process architecture, without the spatial database and tile-server stack originally specified.

**5.3 Recommendations**

Based on the findings of this study, the following recommendations are made:

1. The susceptibility map should be used for relative prioritisation between areas and not for site-specific determinations. The portal's framing as a susceptibility and scenario tool rather than a forecasting instrument should be preserved in any published version, as this is consistent with what the validation demonstrates.

2. Flood incident reporting by LASEMA, NEMA and allied agencies should record coordinates rather than community names alone. The principal obstacle to validating flood models for Lagos is the absence of a geolocated flood inventory, and Section 4.8.4 quantifies the consequence: an otherwise valuable 62-record dataset could support only LGA-level analysis, which proved confounded by population.

3. Drainage and reservoir planning should account for the non-linear discharge response quantified in Table 4.8, in which a 30% rainfall increase produces a 47.6% increase in mean discharge and a 28.2% increase in peak-month discharge at the Ogun outlet.

4. The proposition that the index under-represents urban pluvial flooding should be tested by repeating the overlay analysis with the susceptibility surface stratified by built-up density. If confirmed, a drainage-related factor such as impervious fraction or drainage density should enter the index at a weight materially higher than the 0.05 currently assigned to land cover.

5. Logistic regression or random forest models should be fitted to the same conditioning factors and the same 2012 flood extent, in order to separate the contribution of AHP's uncalibrated weighting from the strictness of the validation design.

6. SUFI-2 should be run over the calibrated parameter set to produce the P-factor and R-factor statistics left unassessed in Table 4.26 and to place confidence bounds on the scenario results.

7. Oyan Dam operation should be incorporated into the model, which would bring the 2022 event within its scope and improve its value for flood early warning, since release-driven events are those for which advance notice is most achievable.

8. Sentinel-1 SAR imagery, offering 10 m all-weather flood mapping, should be used to compile flood extents for several seasons. This would permit validation at a scale appropriate to urban flooding and replace the present single-event assessment.

9. The source of the evapotranspiration seasonality deficiency should be investigated to establish whether it originates in the CHIRPS rainfall forcing, the single-layer soil representation, or the PET formulation, using multi-variable calibration with a widened PET multiplier range.
