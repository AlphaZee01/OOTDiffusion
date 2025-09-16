@echo off
REM OOTDiffusion Health Check Script for Windows

set API_URL=http://localhost:7865
set TIMEOUT=10

echo 🔍 OOTDiffusion Health Check
echo ================================

REM Check if API is running
echo Checking API status...
curl -f -s --max-time %TIMEOUT% "%API_URL%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API is running
    
    echo 📊 Health details:
    curl -s --max-time %TIMEOUT% "%API_URL%/health"
    
    echo.
    echo 🔍 Testing endpoints...
    
    curl -f -s --max-time %TIMEOUT% "%API_URL%/" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Root endpoint
    ) else (
        echo ❌ Root endpoint
    )
    
    curl -f -s --max-time %TIMEOUT% "%API_URL%/docs" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Docs endpoint
    ) else (
        echo ❌ Docs endpoint
    )
    
) else (
    echo ❌ API is not running or not responding
    echo 💡 Try: python quick_start.py
    exit /b 1
)

echo ================================
echo 🎉 Health check completed!
pause
