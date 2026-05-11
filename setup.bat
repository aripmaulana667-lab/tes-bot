@echo off
setlocal ENABLEDELAYEDEXPANSION
title Music Spectrum Lyric Video Maker - Setup

echo ============================================================
echo   Music Spectrum Lyric Video Maker - Windows setup
echo ============================================================
echo.

REM ---------------------------------------------------------------------------
REM 1. Verify Python
REM ---------------------------------------------------------------------------
where python >NUL 2>NUL
if errorlevel 1 (
    where py >NUL 2>NUL
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not on PATH.
        echo         Download Python 3.10+ from https://www.python.org/downloads/
        echo         During install, tick "Add Python to PATH".
        goto :fail
    )
    set "PYCMD=py -3"
) else (
    set "PYCMD=python"
)

for /f "tokens=2 delims= " %%V in ('%PYCMD% --version 2^>^&1') do set "PYVER=%%V"
echo Python detected: !PYVER!

REM ---------------------------------------------------------------------------
REM 2. Virtual environment
REM ---------------------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        goto :fail
    )
) else (
    echo Virtual environment already exists.
)

call .venv\Scripts\activate.bat

REM ---------------------------------------------------------------------------
REM 3. Dependencies
REM ---------------------------------------------------------------------------
echo Upgrading pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] Could not upgrade pip, continuing.
)

echo Installing dependencies from requirements.txt ...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    goto :fail
)

REM ---------------------------------------------------------------------------
REM 4. FFmpeg presence (best-effort)
REM ---------------------------------------------------------------------------
where ffmpeg >NUL 2>NUL
if errorlevel 1 (
    if exist "app\assets\ffmpeg\ffmpeg.exe" (
        echo FFmpeg found in app\assets\ffmpeg.
    ) else (
        echo [WARN] FFmpeg is not detected. Open the app and click
        echo        "Install FFmpeg Online" in the Render tab to auto-download
        echo        a static build, or set the path manually.
    )
) else (
    echo FFmpeg found on PATH.
    ffmpeg -version 2>NUL | findstr /B "ffmpeg version"
)

REM ---------------------------------------------------------------------------
REM 5. Required folders
REM ---------------------------------------------------------------------------
if not exist "output" mkdir "output"
if not exist "temp" mkdir "temp"
if not exist "logs" mkdir "logs"

echo.
echo ============================================================
echo   Setup finished. Run the app with run.bat
echo ============================================================
pause
exit /b 0

:fail
echo.
echo Setup failed. Read the error above before closing this window.
pause
exit /b 1
