@echo off
title 1 - Lagos Flood Portal
cd /d "%~dp0"
echo ================================================================
echo   STEP 1 - STARTING THE LAGOS FLOOD RISK PORTAL
echo.
echo   When it opens, go to your browser at:  http://localhost:8501
echo   Click through EVERY tab once before the defence starts,
echo   so nothing is loading cold during the defence.
echo.
echo   (To stop it later, click this window and press Ctrl + C)
echo ================================================================
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
