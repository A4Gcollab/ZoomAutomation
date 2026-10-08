@echo off
echo ===================================================
echo   YTZ AUTOMATION - PRODUCTION STARTUP
echo ===================================================
echo.
echo [1/4] Cleaning up old processes...
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM uvicorn.exe /T 2>nul

echo.
echo [2/4] Starting Backend (Port 8000)...
start "YTZ Backend" /B python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak >nul

echo.
echo [3/4] Starting Frontend (Port 3000)...
cd frontend
start "YTZ Frontend" /B npm run dev
cd ..
timeout /t 5 /nobreak >nul

echo.
echo [4/4] System Launched!
echo.
echo ---------------------------------------------------
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000/health
echo ---------------------------------------------------
echo.
echo PLEASE OPEN http://localhost:3000 IN YOUR BROWSER.
echo.
pause
