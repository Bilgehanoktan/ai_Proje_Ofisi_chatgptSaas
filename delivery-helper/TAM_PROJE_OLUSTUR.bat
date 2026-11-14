@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 PACK_FULL_0160.py
) else (
  python PACK_FULL_0160.py
)
pause
