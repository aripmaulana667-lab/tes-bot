@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo  Music Spectrum Lyrics Studio - STOP
echo ============================================================

REM Cari semua proses uvicorn / python yang mendengarkan port 3000.
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Menghentikan PID %%P ...
    taskkill /PID %%P /F >nul 2>nul
)

REM Tutup jendela MSLS Backend (kalau ada title cocok).
taskkill /FI "WINDOWTITLE eq MSLS Backend*" /F >nul 2>nul

echo Selesai.
pause
exit /b 0
