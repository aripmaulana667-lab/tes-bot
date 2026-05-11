@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo  Music Spectrum Lyrics Studio - START
echo ============================================================

REM ---------- Validasi setup ----------
if not exist "backend\.venv\Scripts\activate.bat" (
    echo [ERROR] Virtualenv belum dibuat. Jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)
if not exist "frontend\dist\index.html" (
    echo [INFO] Build frontend belum tersedia. Membangun ulang ...
    pushd frontend
    call npm install
    call npm run build || (popd & goto :ERR)
    popd
)

REM ---------- Aktifkan venv ----------
call backend\.venv\Scripts\activate.bat || goto :ERR

REM ---------- Jalankan backend ----------
set PYTHONUNBUFFERED=1
set HOST=127.0.0.1
set PORT=3000

REM Backend serve frontend dist juga di port 3000 -> tunggal proses.
start "MSLS Backend" /MIN cmd /c "cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 3000"

REM Tunggu beberapa detik lalu buka browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo Aplikasi sedang berjalan di http://localhost:3000
echo Tutup window backend untuk menghentikan, atau jalankan stop.bat.
echo.
echo Tekan tombol apa saja untuk menutup window ini (server tetap berjalan).
pause
exit /b 0

:ERR
echo.
echo [ERROR] Gagal memulai aplikasi.
pause
exit /b 1
