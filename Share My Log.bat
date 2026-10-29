@echo off
REM Double-click this if ANYTHING goes wrong, at any point.
REM It makes one text file on your Desktop with everything needed to
REM work out what happened. It contains no personal career information.
title Share My Log
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local\collect-logs.ps1"
if errorlevel 1 pause
