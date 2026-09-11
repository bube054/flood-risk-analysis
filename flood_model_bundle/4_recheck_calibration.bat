@echo off
title 4 - Re-score the calibration
cd /d "%~dp0swat\validation"
echo ================================================================
echo   STEP 4 - RE-SCORING THE CALIBRATION FROM SCRATCH
echo.
echo   Writes the calibrated parameter set, runs the SWAT+ engine,
echo   then scores it against TWO independent variables at once:
echo     discharge -^> GEOGLOWS reach 140585128 (monthly)
echo     ET        -^> basin-mean actual evapotranspiration
echo.
echo   Thesis threshold (Table 3.6) is NSE 0.50 or better.
echo   Takes about 40 seconds.
echo ================================================================
echo.
"..\..\.venv\Scripts\python.exe" calib_joint.py
echo.
echo ================================================================
echo   Done. Press any key to close this window.
echo ================================================================
pause >nul
