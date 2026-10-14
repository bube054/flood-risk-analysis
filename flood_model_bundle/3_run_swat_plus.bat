@echo off
title 3 - Run SWAT+ live
cd /d "C:\SWAT_Ogun\OgunModel2\Scenarios\Default\TxtInOut"
echo ================================================================
echo   STEP 3 - RUNNING THE SWAT+ ENGINE (revision 62)
echo.
echo   Full simulation, 2010 to 2023, Ogun catchment,
echo   outlet at Kara/Akute. Takes about 30 seconds.
echo   Watch the year counter climb.
echo ================================================================
echo.
"C:\Users\bube\SWATPlus\SWATPlusEditor\resources\app.asar.unpacked\static\swat_exe\swatplus-62-ifo-win_amd64-Rel.exe"
echo.
echo ================================================================
echo   The engine just rewrote its output files. Timestamp check:
echo ================================================================
dir channel_sd_mon.txt | find "channel_sd_mon"
echo.
echo   Press any key to close this window.
pause >nul
