@echo off
echo Starting Connection Setup...
echo A browser window will open shortly.
cd /d "%~dp0"
python "scripts\setup_youtube.py"
pause
