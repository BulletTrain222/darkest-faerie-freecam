@echo off
rem Starts the freecam. Double-click this after starting the game in PCSX2.
cd /d "%~dp0"
if defined FREECAM_PYTHON (
  "%FREECAM_PYTHON%" freecam.py
  goto end
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 freecam.py
  goto end
)
where python >nul 2>nul
if not errorlevel 1 (
  python freecam.py
  goto end
)
echo Python wasn't found. Install it from https://www.python.org/downloads/ and try again.
:end
pause
