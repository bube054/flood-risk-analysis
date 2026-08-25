**ABSTRACT**

Flooding is the most frequent and damaging natural hazard affecting Lagos State, Nigeria, yet flood risk information for the state remains fragmented, static, and largely inaccessible to the planners and emergency agencies who need it. This study designed and built an interactive web GIS portal for flood risk analysis and visualisation in Lagos State, supported by process-based hydrological simulation and multi-criteria susceptibility mapping, and validated both components against independent observational data.

Ten geospatial and hydro-meteorological datasets were acquired and harmonised to a 30 m analysis-ready stack in EPSG:32631. A SWAT+ model of the Ogun River catchment, the principal fluvial input to the Lagos Lagoon, was delineated at 19,915 km² across 23 subbasins and 243 hydrologic response units. In the absence of gauged discharge, the model was calibrated against GEOGLOWS ECMWF retrospective discharge at the Kara/Akute outlet, following the data-scarce strategy of Odusanya *et al.* (2019). Flood susceptibility was mapped by Analytical Hierarchy Process weighted overlay of eight conditioning factors, and combined with WorldPop population data to quantify exposure.

The calibrated model achieved Nash–Sutcliffe Efficiency of 0.507, coefficient of determination of 0.606, and percent bias of +1.6% at the monthly time step over 2011–2023, satisfying all three acceptance criteria, with validation-period performance exceeding calibration-period performance. Catchment discharge was found to respond non-linearly to increased rainfall, a 10% rainfall increase producing a 15.5% increase in mean discharge and a 30% increase producing 47.6%. An independent check against two unrelated evapotranspiration products, including MODIS MOD16A2GF satellite retrievals, showed the model reproducing annual evapotranspiration volume to within 14.4% while underestimating its seasonal amplitude by approximately a factor of three.

The susceptibility map placed 4,810,069 residents, representing 38.7% of the state population, within High or Very High susceptibility zones. Validated against an independent MODIS-derived flood extent for the 2012 flood season, the map ranked susceptibility correctly, with observed flooding enriched monotonically across the five zones to 1.61 times chance expectation in the Very High class and 67.08% of observed flood extent falling in the High and Very High zones. However, the map achieved an AUC-ROC of 0.62, sensitivity of 0.685 and overall accuracy of 0.526, failing three of its four acceptance criteria. The map therefore possesses ordinal but not classificatory skill, a limitation attributed to the High and Very High zones jointly covering 48.91% of the state. A secondary validation against NEMA flood records proved confounded, report counts correlating more strongly with raw population than with modelled exposure, and is reported as inconclusive.

A functional portal providing hazard mapping, point query, exposure analysis, rainfall scenario simulation, climate analysis, hydrological results and validation reporting was delivered. The study contributes a calibrated and independently validated hydrological model for the Ogun catchment, a validation design for susceptibility mapping that avoids the circularity common in the literature, and quantified evidence that agency flood-report counts are unsuitable as susceptibility validation data in this setting.

**Keywords:** flood risk, SWAT+, Analytical Hierarchy Process, flood susceptibility, web GIS, Lagos, data-scarce calibration

**ADDITIONAL ABBREVIATIONS**

AOI Area of Interest

CI Consistency Index

CR Consistency Ratio

DFO Dartmouth Flood Observatory

ERA5 Fifth generation ECMWF atmospheric reanalysis

ET Evapotranspiration

GEOGLOWS Global Environmental Observation Global Water Systems

GLO-30 Copernicus Global 30 m Digital Elevation Model

HDX Humanitarian Data Exchange

LULC Land Use and Land Cover

MOD16 MODIS Global Evapotranspiration Product

MODIS Moderate Resolution Imaging Spectroradiometer

NEMA National Emergency Management Agency

PET Potential Evapotranspiration

RI Random Index

SAR Synthetic Aperture Radar

WorldPop WorldPop Global Population Dataset
