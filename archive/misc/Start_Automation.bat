@echo off
echo Starting VONG Automation System...
echo This window will stay open to show you logs.
echo You can also check the 'System_Logs' tab in your Google Sheet.
echo.
cd /d "%~dp0"
python main.py
pause
