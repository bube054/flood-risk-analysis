# Required Corrections to Chapters One to Three

**Prepared from the completed results.** Every item below is a place where the existing text describes something the delivered work did not do, states a figure the results contradict, or conflicts with another part of the same document. Left unchanged, each is a question an examiner can ask that has no good answer.

Items are graded:

- **CRITICAL** — the text describes a procedure that was not followed, or states a target the results miss. Must be fixed.
- **FACTUAL** — a data source or period changed. Straightforward correction.
- **CONSISTENCY** — the document contradicts itself.

---

## CRITICAL 1 — §3.5.5: the calibration procedure described was not the one used

**Current text:** "the study employed SWAT-CUP version 5.2.1 or later (Abbaspour, 2015) for structured calibration, sensitivity analysis, and uncertainty quantification… the study employed the Sequential Uncertainty Fitting version 2 (SUFI-2) algorithm… SUFI-2 performs Latin Hypercube sampling of parameter sets… iteratively narrows the parameter ranges based on the 95% prediction uncertainty band (95PPU)."

**What was actually done:** Calibration was performed by directly writing `calibration.cal`, invoking the SWAT+ executable, and scoring each candidate set against monthly GEOGLOWS discharge. No SWAT-CUP, no SUFI-2, no Latin Hypercube sampling, and no 95PPU band was produced.

**Why this matters most:** This is the single largest gap between the methodology and the work. It also cascades — Table 3.6 lists P-factor ≥ 0.70 and R-factor ≤ 1.5 as acceptance criteria, and both are outputs of SUFI-2's uncertainty band. Neither can be reported.

**Suggested replacement:**

> Calibration was performed through iterative manual adjustment of the SWAT+ calibration file (`calibration.cal`), with each candidate parameter set evaluated by direct execution of the SWAT+ engine (revision 62) and scored against monthly GEOGLOWS discharge at the catchment outlet using NSE, R² and PBIAS. This approach was adopted in preference to SWAT-CUP/SUFI-2 because the calibration target was a modelled rather than gauged series, for which a formal uncertainty band around the observations cannot be meaningfully interpreted, and because the small number of sensitive parameters identified during preliminary testing did not warrant automated global optimisation. The consequence is that P-factor and R-factor statistics were not produced; this is recorded as a limitation.

**Also:** Table 3.2 lists CN2, ALPHA_BF, GW_DELAY, GWQMN, GW_REVAP, ESCO and SOL_AWC. These are SWAT2012 parameter names. The parameters actually calibrated in SWAT+ rev-62 were `perco`, `petco`, `canmx`, `alpha`, `flo_min` and `bf_max`. Replace Table 3.2 with the parameters and ranges actually used, and note that `esco`, `epco` and `awc` were tested and found either inert or counter-productive in this SWAT+ revision.

---

## CRITICAL 2 — §3.5.4 and §3.8.1: the simulation periods are wrong

**Current text (§3.5.4):** warm-up 2001–2003; calibration 2004–2013; validation 2014–2020; baseline 2004–2020.
**Current text (§3.8.1):** "The calibrated model will be run over the independent validation period (2014–2020)…"

**What was actually done:** Simulation 2010–2023 with a one-year warm-up (`nyskip = 1`); evaluation 2011–2023; **calibration 2011–2017; validation 2018–2023.**

**Why the change was necessary:** The CHIRPS and ERA5-Land weather series were extracted for 2010–2023. A 2004 start would have required an additional decade of forcing data that was not assembled.

**Action:** Replace every period reference in §3.5.4 and §3.8.1 with the actual windows. This appears in at least two places; check for others.

---

## CRITICAL 3 — §1.3 Objectives (iii) and (v) vs §3.8.2 and Table 3.6: two different AUC targets, and both are missed

**The internal contradiction:**

- §1.3 Objective (iii): "a target AUC-ROC of 0.75 or above and sensitivity of at least 70%"
- §1.3 Objective (v): "susceptibility map AUC-ROC greater than or equal to 0.75"
- §3.8.2 Step 2: "the target was set at an AUC > 0.70 as the minimum acceptable performance"
- Table 3.6: "AUC-ROC > 0.70 (acceptable)"

The document sets two different thresholds for the same metric. Fix this regardless of the result.

**The measured result:** AUC-ROC = **0.62**, sensitivity = **0.685**, overall accuracy = **0.526**. The map misses 0.75 and 0.70 alike, and misses three of the four criteria in Table 3.6.

**What to do.** Do not quietly lower the threshold to match the result — that is visible in the version history and is worse than the shortfall. State one threshold consistently, report the outcome as obtained, and use §4.9.4 of Chapter Four, which sets out three specific reasons the validation design here is stricter than most published studies.

**Suggested rewording of Objective (iii)'s success criterion:**

> …and to validate the maps against an independent flood inventory, reporting AUC-ROC, sensitivity, specificity and overall accuracy against the acceptance criteria of Table 3.6, with an AUC-ROC above 0.70 taken as the threshold for acceptable discrimination.

This states the target and commits to reporting the result, without promising an outcome the data does not support.

---

## CRITICAL 4 — §1.3 Objective (iv) and all of §3.7: the portal architecture described was not built

**Current text (Objective iv):** "built on PostgreSQL/PostGIS, GeoServer, FastAPI, React, and Leaflet, and deployable via Docker containers."
**Current text (§3.7.1):** three-tier architecture with PostGIS, GeoServer serving WMS/WFS/WCS, FastAPI REST API, React single-page application, Celery with Redis, all containerised under Docker Compose.

**What was actually built:** A Streamlit application over a single Python API module (`model_api.py`), with Folium/Leaflet for the interactive map. No PostGIS, GeoServer, FastAPI, React, Celery, Redis or Docker.

**Scale of the problem:** §3.7 runs from 3.7.1 to 3.7.5 and describes the unbuilt architecture in detail, including database schemas and container orchestration. This is several pages describing software that does not exist.

**Two honest options.**

*Option A — rewrite §3.7 to describe what was built.* Faster and defensible. The five required features all exist; only the stack differs. Justify it: the outputs are static raster and tabular products needing neither a spatial database nor a tile server, and a single-process application deploys on the available hardware without orchestration.

*Option B — build the specified stack.* Substantially more work and, for this data, delivers no analytical benefit.

**Recommendation: Option A.** Reword Objective (iv) to require five core features and an interactive map, without naming a specific stack, and rewrite §3.7 around the Streamlit implementation. Chapter Four §4.7 already documents the deviation; the methodology chapter needs to agree with it.

---

## CRITICAL 4b — §3.6.3 Table 3.4: the pairwise matrix describes a different model

**Current text:** Table 3.4 gives an 8×8 pairwise comparison matrix over the factors Elev, Slope, FlowAcc, DistRiv, LandCov, **Soil**, Rain and **SWAT**, followed by the note: *"This is an illustrative matrix. Final values will be refined based on literature synthesis and sensitivity analysis."*

**Two problems.**

*First, the factor set is wrong.* The delivered model uses elevation, **TWI**, distance to rivers, flow accumulation, **runoff (SCS-CN)**, slope, extreme rainfall and land cover. Table 3.4 contains **Soil** and **SWAT**, neither of which is a factor in the delivered index, and omits **TWI**, which carries the second-heaviest weight at 0.18. The matrix cannot have produced the weights that were used.

*Second, it is labelled illustrative.* A thesis cannot report a Consistency Ratio derived from a matrix it describes as provisional.

**What the numbers show.** Table 3.4 as printed is perfectly reciprocal and is internally consistent, giving **CR = 0.0074**. But its weights are:

| Factor | Table 3.4 weight | Delivered weight |
|---|---|---|
| DistRiv | **0.259** (highest) | 0.15 |
| Elev | 0.190 | **0.20** (highest) |
| FlowAcc | 0.111 | 0.12 |
| Rain | 0.111 | 0.08 |
| Slope | 0.106 | 0.10 |
| SWAT | 0.106 | — (not a factor) |
| LandCov | 0.060 | 0.05 |
| Soil | 0.058 | — (not a factor) |
| TWI | — (absent) | **0.18** |

Table 3.4 makes distance to rivers the dominant factor; the delivered model makes elevation dominant and TWI second.

**Action.** Replace Table 3.4 with the matrix over the eight factors actually used, remove the "illustrative" note, and report its CR. Chapter Four §4.7.1 now contains such a matrix, giving **CR = 0.0115** against the criterion of ≤ 0.10, and reproducing the applied weights to within 0.012.

**Important:** that matrix was reconstructed from the weights, because the original is not recorded anywhere in the project files. If you still have the matrix you actually built, use it instead — that is the correct route. If you do not, review every judgement in the reconstructed matrix against your own reasoning before adopting it, and re-run `validation/ahp_consistency.py` after any change. The judgements have to be ones you can defend orally.

Do not be tempted to build the matrix as exactly a_ij = w_i/w_j. That produces CR = 0.000 for any weight vector whatsoever and demonstrates nothing; the script shows this case explicitly.

---

## FACTUAL 5 — §3.3.2: the DEM was Copernicus GLO-30, not SRTM

**Current text:** "the study employed the Shuttle Radar Topography Mission (SRTM) Digital Elevation Model (DEM) for this study. **Dataset:** SRTM DEM Version 3.0 (SRTM GL1)…"

**What was used:** Copernicus GLO-30 DEM, 30 m, from the AWS open bucket `copernicus-dem-30m`, mosaicked from six tiles and resampled to 90 m for delineation.

**The justification (use it — it is a good one):** The available SRTM tiles did not extend north of 7°N and therefore did not cover the Ogun headwaters, which reach approximately 8.95°N. Copernicus GLO-30 provides equivalent resolution with complete basin coverage and open access without registration.

**Also note** the 90 m resampling for delineation, and why: the 30 m DEM (81 million cells) stalled TauDEM's D8 flow-direction routine, and 90 m is standard practice for a catchment of roughly 20,000 km².

**Action:** Rewrite §3.3.2 around Copernicus GLO-30. Update Objective (i), which names "SRTM DEM". Check §3.4.2 for consequential references.

---

## FACTUAL 6 — §3.3.6: NIHSA discharge was not obtained; GEOGLOWS was used

**Current text:** NIHSA is named as the primary source, with a contingency of "a regionalization approach… using published calibrated SWAT parameters from similar catchments."

**What happened:** NIHSA data was not obtained within the project period. The contingency invoked was **not** the regionalisation approach described, but calibration against **GEOGLOWS v2 ECMWF retrospective discharge** at reach 140585128 (Ogun at Kara/Akute) — 31,589 daily values, 1940–2026, aggregated to monthly.

**Action:** Rewrite §3.3.6 to state GEOGLOWS as the calibration reference actually used. Keep the NIHSA request on record as attempted — it strengthens the account. Replace the regionalisation contingency with the strategy followed, citing Odusanya *et al.* (2019) as the data-scarce precedent already in your Chapter Two.

**State plainly** that GEOGLOWS is a modelled product, so the performance statistics measure agreement between two models rather than agreement with observation. Chapter Four §4.9.2 develops this, and §4.4 shows how the independent ET validation partially offsets it. Raising this yourself is far stronger than having it raised for you.

**Also:** Table 3.6 lists "Observed discharge (NIHSA)" as the data source for three SWAT metrics. Change to GEOGLOWS.

---

## FACTUAL 7 — §3.3.7: the flood inventory needs to describe what was actually compiled

The delivered validation used two datasets, both from open archives:

1. **MODIS 250 m flood extent, Nigeria, July–November 2012** (NASA/DFO, via HDX) — 35.2 km² across 290 discrete patches within Lagos. Permanent water is masked in the source product, so this represents detected flooding rather than the lagoon.
2. **NEMA 2022 flood records** (via HDX) — 62 community-level reports across 13 of the 20 Lagos LGAs.

**Record explicitly that no geocoding was attempted.** NEMA records carry community names but no coordinates, and assigning coordinates from place names would inject fabricated locations into the dataset used for validation. The records were therefore used only at LGA level. This is a deliberate methodological decision and should read as one.

**Also update §3.8.2**, which assumes "geocoded flood inventory points". The pixel-level validation used a continuous flood *extent*, not points — a stricter test, and worth saying so.

---

## FACTUAL 8 — Table 3.6: two criteria cannot be reported

P-factor (≥ 0.70) and R-factor (≤ 1.5) are SUFI-2 outputs. Since SUFI-2 was not used (CRITICAL 1), neither exists.

**Action:** Either remove both rows, or retain them marked "not assessed — no uncertainty ensemble generated" with a cross-reference to the limitations section. Retaining them is more transparent.

**Also update the data-source column** from NIHSA to GEOGLOWS, and add a row for the independent ET validation, which is a genuine addition to the validation strategy and currently appears nowhere in Chapter Three.

---

## CONSISTENCY 9 — §3.8.1: three checks are described that were not performed

**Current text:** "(a) visual comparison of observed and simulated monthly hydrographs; (b) comparison of simulated annual water balance components against literature-reported values for the Ogun River basin; and (c) comparison of simulated peak discharge timing with documented flood event dates from LASEMA records."

- (a) **was** done — Table 4.3 in Chapter Four.
- (b) was **not** done against literature values. However, the ET validation in §4.4 is a stronger version of the same idea, testing a water-balance component against two independent gridded products rather than against published figures. Reword (b) to describe that.
- (c) was **not** done. No LASEMA event-date comparison was performed. Either remove it or carry it into further work.

---

## CONSISTENCY 10 — §3.6 and §1.3: the SWAT-derived runoff layer was not integrated

§3.4 describes a "SWAT-derived runoff indicator" feeding the AHP overlay. In the delivered model, the `runoff` factor (weight 0.12) remains the **SCS Curve Number** calculation. SWAT+ results are presented in their own portal panel rather than substituted into the susceptibility index.

**This is defensible** — SWAT covers one catchment while the map is statewide, so substituting a single-catchment output into a statewide index would be unsound. But say so, rather than leaving the text implying an integration that did not occur.

---

## What to add to §1.6 (Limitations)

Four items from the completed work belong in the limitations section:

1. **No gauged discharge.** Calibration used modelled GEOGLOWS discharge; statistics measure inter-model agreement.
2. **Oyan Dam not represented.** It lies within the modelled basin. The 2022 flood was substantially release-driven and falls outside the model's scope.
3. **Single-layer soil.** SoilGrids 0–5 cm topsoil texture only; 88% of the basin assigned to one class; no vertical structure.
4. **Single-event spatial validation.** The map is a static surface tested against one flood season at 250 m resolution, which cannot resolve street-scale urban flooding.

---

## Suggested order of work

1. **CRITICAL 4** (§3.7 portal architecture) — largest volume of text.
2. **CRITICAL 1** (§3.5.5 calibration procedure) — including Table 3.2 and the P/R-factor consequence.
3. **CRITICAL 4b** (§3.6.3 Table 3.4 pairwise matrix) — replace with the matrix over the eight factors actually used.
4. **CRITICAL 3** (AUC threshold) — reconcile the contradiction, one number throughout.
5. **CRITICAL 2** (simulation periods) — mechanical, quick.
6. **FACTUAL 5–8** — data sources, mostly localised edits.
7. **CONSISTENCY 9–10** and the §1.6 additions.

---

## A closing note on the shortfall

Three of the four susceptibility criteria were missed. That is not a failed project, and it should not be presented as one.

The map does what a susceptibility map is principally for: it ranks. Enrichment rises monotonically across all five zones, reaching 1.61 times chance in the Very High class. What it cannot do is separate flooded from non-flooded ground at a single threshold, because the High and Very High zones together cover 48.9% of Lagos.

That result was obtained against an independent satellite flood extent that played no part in building the map — a materially stricter test than the point inventories most published studies validate against, which are often implicated in the weighting they then validate. The honest reading is that a strict test produced a modest number, and Chapter Four sets out both the mechanism and the specific further work that would distinguish model limitation from validation severity.

Report it as measured. A validation that confirmed every expectation would be weaker evidence of rigour than one that located the limits.
