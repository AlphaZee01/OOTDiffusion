@echo off
REM OOTDiffusion Model Checkpoint Downloader for Windows
echo 🎭 OOTDiffusion Model Checkpoint Downloader
echo ================================================

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first.
    echo    Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if git-lfs is available
git lfs version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  git-lfs is not installed. Installing...
    echo    Please install git-lfs manually:
    echo    1. Download from: https://git-lfs.github.io/
    echo    2. Run the installer
    echo    3. Restart your terminal
    echo    4. Run this script again
    pause
    exit /b 1
)

echo ✅ Git and git-lfs are available

REM Initialize git-lfs
echo 🔄 Initializing git-lfs...
git lfs install

REM Create checkpoints directory
if not exist "checkpoints" mkdir checkpoints
cd checkpoints

echo.
echo 📥 Downloading model checkpoints...
echo.

REM Download OOTDiffusion models
echo 📥 Downloading OOTDiffusion models...
if not exist "ootd" (
    git clone https://huggingface.co/levihsu/OOTDiffusion ootd
    if %errorlevel% neq 0 (
        echo ❌ Failed to download OOTDiffusion models
        goto :error
    )
) else (
    echo ✅ OOTDiffusion models already exist
)

REM Download human parsing models
echo 📥 Downloading human parsing models...
if not exist "humanparsing" (
    git clone https://huggingface.co/levihsu/OOTDiffusion humanparsing
    if %errorlevel% neq 0 (
        echo ❌ Failed to download human parsing models
        goto :error
    )
) else (
    echo ✅ Human parsing models already exist
)

REM Download OpenPose models
echo 📥 Downloading OpenPose models...
if not exist "openpose" (
    git clone https://huggingface.co/levihsu/OOTDiffusion openpose
    if %errorlevel% neq 0 (
        echo ❌ Failed to download OpenPose models
        goto :error
    )
) else (
    echo ✅ OpenPose models already exist
)

REM Download CLIP models
echo 📥 Downloading CLIP models...
if not exist "clip-vit-large-patch14" (
    git clone https://huggingface.co/openai/clip-vit-large-patch14
    if %errorlevel% neq 0 (
        echo ❌ Failed to download CLIP models
        goto :error
    )
) else (
    echo ✅ CLIP models already exist
)

cd ..

echo.
echo ================================================
echo 🎉 All models downloaded successfully!
echo.
echo 📋 Next steps:
echo 1. Run setup: scripts\setup.bat
echo 2. Start API: python start.py --mode api
echo 3. Open test_interface.html to test
echo.
pause
exit /b 0

:error
echo.
echo ❌ Download failed. Please check your internet connection and try again.
echo.
pause
exit /b 1
