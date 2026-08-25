# Independent Validation

Checks the models were **not** fitted to. Read this before quoting any number below.

The headline: **the results are mixed, and one is a null result.** That is a normal and
defensible outcome — validation that only ever confirms is not validation. Present these as
found; do not round them up.

---

## What was tested, and what came back

| # | Test | Observation | Result | Verdict |
|---|------|-------------|--------|---------|
| 1 | SWAT+ evapotranspiration | **MODIS MOD16**, 155 months | NSE 0.09 · R² 0.35 · PBIAS +15.7% | **Partial** — volume good, dynamics fail |
| 1b | same, second reference | TerraClimate AET, 155 months | NSE 0.18 · R² 0.39 · PBIAS +12.5% | **Agrees with MOD16** |
| 2 | Discharge-vs-ET trade-off | both objectives scored together | incumbent is the only feasible set | **Parameters retained** |
| 3 | Hazard map, pixel level | MODIS 2012 flood extent, 35.2 km² | AUC-ROC 0.62 · enrichment 1.37× | **Modest but real skill** |
| 4 | Hazard map, LGA level | NEMA 2022, 62 Lagos reports | ρ = −0.45 vs exposure, **+0.57 vs population** | **Inconclusive / null** |

---

## The two things most likely to be challenged

**1. The ET seasonality is badly off, and you should say so first.** Against MODIS, SWAT+
swings only ~26 mm across the year where MODIS swings ~81 mm — the seasonal amplitude is
about **3× too flat**. Annual volume is fine (+15.7%, inside the ±25% band), so the model
moves roughly the right amount of water; it just spreads it too evenly through the year.

Expect to be asked why. The honest answer is in §11.2 of the methodology log: `petco`, the
PET multiplier, is pinned at its allowed ceiling of 1.20, and pushing past it improves ET
but breaks the discharge thresholds. The two objectives genuinely conflict.

**Both ET references agree**, which is the strongest part of this. MODIS (935 mm/yr,
satellite) and TerraClimate (900 mm/yr, water-balance model) were run independently and show
the same damped cycle. A single reference could be wrong; two unrelated ones agreeing is
much harder to dismiss.

**2. Test B is confounded, and saying so is the correct move.** NEMA report counts correlate
with raw population (ρ = +0.57) far better than with modelled exposure (ρ = +0.17). The
dataset largely measures where reporting happens, not where flooding happens. It cannot
validate the map in either direction.

The negative ρ against exposure fraction (−0.45) is *worth raising as a hypothesis*, not a
finding: the AHP index is topography-driven (elevation 0.20 + TWI 0.18), while much Lagos
flooding is drainage-failure pluvial flooding in dense inland LGAs (Alimosho, Agege,
Ifako-Ijaye all rank low in the model yet generated the most reports). That is a plausible
structural blind spot in an AHP susceptibility approach and a strong "further work" point.

---

## Files

| File | What it does |
|---|---|
| `spatial_validation.py` | Tests A + B. Self-contained; writes `spatial_validation_results.json`. |
| `build_validation_bundle.py` | Merges all results into `models/core/validation_results.json` for the portal. |
| `nema_2022_lagos.csv` | The 62 extracted Lagos NEMA records (state, LGA, community, date, affected). |
| `../swat/validation/et_validation.py` | ET comparison against TerraClimate. |
| `../swat/validation/calib_joint.py` | Scores a parameter set against discharge **and** ET at once. |
| `../swat/validation/fetch_mod16_et_gee.js` | GEE script for the true MOD16 version. |

Reproduce everything:

```bash
python ../swat/validation/et_validation.py && python spatial_validation.py && python build_validation_bundle.py
```

---

## Sources (cite these)

- **MODIS flood extent** — Nigeria flood extents Jul–Nov 2012, NASA/DFO, via HDX
  (`Nigeria - Flood Extents Nov 2012`). 250 m.
- **NEMA flood records** — 2022 NEMA Flood Data, via HDX (`Nigeria: Flood data`).
  62 Lagos community reports across 13 LGAs.
- **TerraClimate** — Abatzoglou, J.T. et al. (2018) *Scientific Data* 5:170191. ~4 km monthly.
- **GEOGLOWS** — ECMWF retrospective discharge, reach 140585128 (Ogun @ Kara).
- **Method precedent** — Odusanya, A.E. et al. (2019), multi-variable SWAT calibration with
  satellite ET in a data-scarce southwestern Nigerian catchment.
- **Evaluation thresholds** — Moriasi, D.N. et al. (2007), monthly time step.

## What is NOT claimed

None of this establishes forecast skill. The map remains an AHP **susceptibility** index with
a measured, modest correspondence to one observed flood event. It does not predict when or
whether a specific flood will occur.
