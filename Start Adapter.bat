@echo off
REM Double-click this every time you want to work on your job search.
title Adapter
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local\start-windows.ps1"
if errorlevel 1 (
  echo.
  echo Adapter exited with an error. Run Share My Log.bat and send the file.
  pause
)
