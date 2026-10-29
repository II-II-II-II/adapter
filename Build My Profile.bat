@echo off
REM Double-click this after you have finished your interview and
REM downloaded the chat.
title Build My Profile
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local\build-profile.ps1"
if errorlevel 1 (
  echo.
  echo That exited with an error. Run Share My Log.bat and send the file.
  pause
)
