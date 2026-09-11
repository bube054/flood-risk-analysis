@echo off
title 6 - Validate MY hand-rebuilt map against the published one
cd /d "%~dp0"
echo ================================================================
echo   BLOCK 9 - DOES MY REBUILD VALIDATE LIKE THE PUBLISHED MAP?
echo.
echo   Runs the thesis Test A (Section 3.8.2) twice - once on the
echo   published map, once on the map rebuilt by hand in QGIS -
echo   against the MODIS 250m observed flood extent for Lagos,
echo   July to November 2012.
echo.
echo   Reads:  Desktop\aligned\FSI.tif
echo           Desktop\aligned\hazard_zones.tif
echo ================================================================
echo.
".venv\Scripts\python.exe" validation\validate_rebuild.py %1
echo.
echo ================================================================
echo   Done. Press any key to close this window.
echo ================================================================
pause >nul
