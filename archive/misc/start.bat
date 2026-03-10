@echo off
echo ========================================
echo YTZ Automation - Quick Start
echo ========================================
echo.

echo [1/3] Starting Backend...
start "YTZ Backend" cmd /k "python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend...
cd frontend
start "YTZ Frontend" cmd /k "npm run dev"
cd ..
timeout /t 3 /nobreak >nul

echo [3/3] Opening Browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================
echo ✅ YTZ Automation Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop all services...
pause >nul

echo.
echo Stopping services...
taskkill /FI "WINDOWTITLE eq YTZ Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq YTZ Frontend*" /T /F >nul 2>&1

echo.
echo All services stopped.
pause
