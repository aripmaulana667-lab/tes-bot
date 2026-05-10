@echo off
setlocal
chcp 65001 >nul

echo ============================================================
echo  LiveStream Server - Setup
echo ============================================================

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan di PATH.
    echo Install Python 3.10+ dari https://python.org dan centang
    echo "Add Python to PATH" pada saat install.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/3] Membuat virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Gagal membuat virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment sudah ada, lewati pembuatan.
)

echo [2/3] Upgrade pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] Gagal upgrade pip, lanjut tetap pakai versi lama.
)

echo [3/3] Install dependency dari requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Gagal install dependency.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup selesai. Jalankan run.bat untuk start server.
echo ============================================================
pause
endlocal
