@echo off
title ClipFlow Studio - Setup
echo ============================================================
echo   ClipFlow Studio - Setup
echo   AI-Powered Smart Video Clipper
echo ============================================================
echo.

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo [1/6] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python 3.11+ is installed and on PATH.
        pause
        exit /b 1
    )
) else (
    echo [1/6] Virtual environment already exists.
)

REM Activate venv
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [2/6] Upgrading pip...
python -m pip install --upgrade pip

echo [3/6] Installing Python dependencies (this may take a while)...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install.
    echo You can re-run setup.bat later or install missing
    echo packages from inside the app (Dependency Status page).
)

echo [4/6] Creating runtime folders...
if not exist outputs mkdir outputs
if not exist temp mkdir temp
if not exist assets mkdir assets
if not exist tools mkdir tools
if not exist tools\ffmpeg mkdir tools\ffmpeg
if not exist tools\deno mkdir tools\deno

echo [5/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg belum terinstall atau belum masuk PATH.
    echo FFmpeg bisa diinstall otomatis dari dalam aplikasi.
) else (
    echo FFmpeg ditemukan ^(global^).
)
if exist tools\ffmpeg\bin\ffmpeg.exe (
    echo FFmpeg lokal ditemukan di tools\ffmpeg\bin\ffmpeg.exe.
)

echo [6/6] Checking Deno...
deno --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Deno belum terinstall atau belum masuk PATH.
    echo Deno bisa diinstall otomatis dari dalam aplikasi.
) else (
    echo Deno ditemukan ^(global^).
)
if exist tools\deno\deno.exe (
    echo Deno lokal ditemukan di tools\deno\deno.exe.
)

echo.
echo ============================================================
echo   Setup selesai. Jalankan run.bat untuk membuka aplikasi.
echo ============================================================
pause
