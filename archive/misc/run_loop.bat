@echo off
cd /d "%~dp0"
title VONG Automation Monitor

:loop
cls
echo [%DATE% %TIME%] Starting VONG Automation System...
echo ---------------------------------------------------
python main.py
echo ---------------------------------------------------
echo [%DATE% %TIME%] Application exited unexpectedly!
echo Restarting in 10 seconds... (Press Ctrl+C to stop)
timeout /t 10 /nobreak >nul
goto loop
