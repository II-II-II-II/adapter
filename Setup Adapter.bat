@echo off
REM Double-click this to install Adapter.
REM It runs local\setup-windows.ps1 without you having to change any
REM Windows security settings by hand.
title Adapter Setup
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local\setup-windows.ps1"
REM If PowerShell itself failed, the script never reached its own prompt.
if errorlevel 1 (
  echo.
  echo Setup exited with an error. See the logs folder, or run Share My Log.bat
  pause
)
