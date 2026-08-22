@echo off
title Lagos Flood Portal
cd /d "%~dp0"
echo ================================================================
echo   Starting the Lagos Flood Risk Portal...
echo   When it opens, go to your browser at:  http://localhost:8501
echo   (To stop it later, click this window and press  Ctrl + C )
echo ================================================================
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
