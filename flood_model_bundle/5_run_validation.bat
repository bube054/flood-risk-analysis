@echo off
title 5 - Independent validation checks
cd /d "%~dp0"
echo ================================================================
echo   STEP 5a - MAP VALIDATION vs THE MODIS 2012 FLOOD EXTENT
echo   Rebuilds the ROC curve, the confusion matrix and the
echo   per-zone enrichment ratios. (Tables 4.20 and 4.21)
echo ================================================================
echo.
".venv\Scripts\python.exe" validation\spatial_validation.py
echo.
echo ================================================================
echo   STEP 5b - AHP CONSISTENCY
echo   Recomputes lambda-max, CI and the consistency ratio.
echo   (Table 4.15 - CR = 0.0115, threshold is 0.10)
echo ================================================================
echo.
".venv\Scripts\python.exe" validation\ahp_consistency.py
echo.
echo ================================================================
echo   STEP 5c - INDEPENDENT EVAPOTRANSPIRATION CHECK
echo   Scores the model against MODIS MOD16 satellite ET,
echo   which was NEVER used in calibration. (Tables 4.10 to 4.12)
echo ================================================================
echo.
cd /d "%~dp0swat\validation"
"..\..\.venv\Scripts\python.exe" et_validation.py --reference mod16_et_ogun_monthly_basin.csv
echo.
echo ================================================================
echo   All three checks done. Press any key to close this window.
echo ================================================================
pause >nul
