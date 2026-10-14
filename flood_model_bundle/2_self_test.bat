@echo off
title 2 - Model self-test
cd /d "%~dp0"
echo ================================================================
echo   STEP 2 - MODEL SELF-TEST
echo.
echo   Recomputes the headline numbers from Chapter Four:
echo   design rainfall, point query, exposure, SWAT+ calibration,
echo   the ET check and the map AUC.
echo ================================================================
echo.
".venv\Scripts\python.exe" model_api.py
echo.
echo ================================================================
echo   Done. Press any key to close this window.
echo ================================================================
pause >nul
