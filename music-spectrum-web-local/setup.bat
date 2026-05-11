@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo  Music Spectrum Lyrics Studio - SETUP
echo ============================================================
echo.

REM ---------- Cek Python ----------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan di PATH.
    echo Silakan install Python 3.10+ dari https://www.python.org/downloads/windows/
    echo Pastikan centang "Add python.exe to PATH" saat instalasi.
    pause
    exit /b 1
)

REM ---------- Cek Node ----------
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js tidak ditemukan di PATH.
    echo Silakan install Node.js 18+ dari https://nodejs.org/en/download
    pause
    exit /b 1
)

REM ---------- Backend ----------
echo [1/4] Membuat virtualenv Python ...
if not exist "backend\.venv" (
    python -m venv backend\.venv || goto :ERR
)
call backend\.venv\Scripts\activate.bat || goto :ERR

echo [2/4] Menginstal dependensi backend ...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt || goto :ERR

REM ---------- Frontend ----------
echo [3/4] Menginstal dependensi frontend ...
pushd frontend
call npm install || (popd & goto :ERR)

echo [4/4] Build frontend (produksi) ...
call npm run build || (popd & goto :ERR)
popd

REM ---------- .env ----------
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
)

REM ---------- Folder storage ----------
for %%D in (music lyrics backgrounds logos outputs temp) do (
    if not exist "storage\%%D" mkdir "storage\%%D"
)
if not exist "tools\ffmpeg" mkdir "tools\ffmpeg"

echo.
echo ============================================================
echo  Setup selesai!
echo  Selanjutnya jalankan start.bat untuk membuka aplikasi.
echo ============================================================
pause
exit /b 0

:ERR
echo.
echo [ERROR] Setup gagal. Periksa pesan di atas.
pause
exit /b 1
