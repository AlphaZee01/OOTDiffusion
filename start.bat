@echo off
echo 🎭 OOTDiffusion - Quick Start
echo ==============================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "quick_start.py" (
    echo ❌ quick_start.py not found
    echo Please run this script from the OOTDiffusion directory
    pause
    exit /b 1
)

echo 🚀 Starting OOTDiffusion...
python quick_start.py
pause
