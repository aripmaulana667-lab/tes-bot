@echo off
setlocal enabledelayedexpansion
title ClipFlow Studio - Setup

REM Always run from the directory that contains this script,
REM so it works whether double-clicked or launched from another folder.
cd /d "%~dp0"

set "LOGFILE=%~dp0setup.log"
> "%LOGFILE%" echo ClipFlow Studio setup log
>>"%LOGFILE%" echo Date: %date% %time%
>>"%LOGFILE%" echo.

echo ============================================================
echo   ClipFlow Studio - Setup
echo   AI-Powered Smart Video Clipper
echo ============================================================
echo Output detail juga disimpan ke setup.log
echo (lampirkan file ini kalau ada error).
echo.

REM ----------------------------------------------------------------
REM Step 0: Detect a real Python (not the Microsoft Store stub).
REM ----------------------------------------------------------------
set "PYCMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYCMD=py -3"
)

if not defined PYCMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%P in ('where python') do (
            echo %%P | findstr /i "WindowsApps" >nul
            if errorlevel 1 (
                if not defined PYCMD set "PYCMD=%%P"
            )
        )
    )
)

if not defined PYCMD (
    echo [ERROR] Python tidak ditemukan di PATH.
    echo.
    echo Solusi:
    echo   1. Install Python 3.11+ dari https://www.python.org/downloads/
    echo   2. Saat install centang ^"Add Python to PATH^".
    echo   3. Tutup CMD, buka lagi, lalu jalankan setup.bat.
    echo.
    echo Catatan: ^"python^" dari Microsoft Store sering tidak bisa
    echo membuat virtual environment. Pakai installer resmi python.org.
    >>"%LOGFILE%" echo [ERROR] Python tidak ditemukan
    goto :end
)

echo [0/6] Python: %PYCMD%
>>"%LOGFILE%" echo Python interpreter: %PYCMD%
%PYCMD% --version
%PYCMD% --version >>"%LOGFILE%" 2>&1
echo.

REM ----------------------------------------------------------------
REM Step 1: Create venv
REM ----------------------------------------------------------------
if not exist venv (
    echo [1/6] Membuat virtual environment ^(venv^)...
    >>"%LOGFILE%" echo [step] create venv
    %PYCMD% -m venv venv >>"%LOGFILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Gagal membuat virtual environment.
        echo Buka setup.log untuk detail error.
        goto :end
    )
) else (
    echo [1/6] Virtual environment sudah ada.
)

if not exist venv\Scripts\python.exe (
    echo [ERROR] venv\Scripts\python.exe tidak ada.
    echo Hapus folder ^"venv^" lalu jalankan setup.bat lagi.
    >>"%LOGFILE%" echo [ERROR] venv missing python.exe
    goto :end
)

set "VENVPY=%~dp0venv\Scripts\python.exe"

REM ----------------------------------------------------------------
REM Step 2: Upgrade pip
REM ----------------------------------------------------------------
echo [2/6] Upgrade pip...
>>"%LOGFILE%" echo [step] upgrade pip
"%VENVPY%" -m pip install --upgrade pip >>"%LOGFILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Gagal upgrade pip ^(setup tetap dilanjutkan^). Lihat setup.log.
)

REM ----------------------------------------------------------------
REM Step 3: Install Python dependencies
REM ----------------------------------------------------------------
echo [3/6] Install dependency Python ^(bisa lama, ratusan MB^)...
echo Output detail ada di setup.log.
>>"%LOGFILE%" echo [step] pip install -r requirements.txt
"%VENVPY%" -m pip install -r requirements.txt >>"%LOGFILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Sebagian dependency gagal terinstall.
    echo Aplikasi tetap bisa dibuka via run.bat; install ulang
    echo dari halaman ^"Dependency Status^" di dalam aplikasi,
    echo atau jalankan setup.bat lagi setelah memperbaiki internet.
    echo Lihat setup.log untuk detail error.
) else (
    echo [3/6] Dependency Python OK.
)

REM ----------------------------------------------------------------
REM Step 4: Buat folder runtime
REM ----------------------------------------------------------------
echo [4/6] Membuat folder runtime...
if not exist outputs mkdir outputs
if not exist temp mkdir temp
if not exist assets mkdir assets
if not exist tools mkdir tools
if not exist tools\ffmpeg mkdir tools\ffmpeg
if not exist tools\deno mkdir tools\deno
if not exist config mkdir config

REM ----------------------------------------------------------------
REM Step 5: Cek FFmpeg
REM ----------------------------------------------------------------
echo [5/6] Cek FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   FFmpeg ^(global^) belum terdeteksi di PATH.
    echo   Bisa diinstall otomatis dari halaman Dependency Status.
) else (
    echo   FFmpeg ^(global^) OK.
)
if exist tools\ffmpeg\bin\ffmpeg.exe (
    echo   FFmpeg lokal: tools\ffmpeg\bin\ffmpeg.exe.
)

REM ----------------------------------------------------------------
REM Step 6: Cek Deno
REM ----------------------------------------------------------------
echo [6/6] Cek Deno ^(opsional, hanya helper fallback^)...
deno --version >nul 2>&1
if errorlevel 1 (
    echo   Deno ^(global^) belum terdeteksi di PATH.
    echo   Bisa diinstall otomatis dari halaman Dependency Status.
) else (
    echo   Deno ^(global^) OK.
)
if exist tools\deno\deno.exe (
    echo   Deno lokal: tools\deno\deno.exe.
)

echo.
echo ============================================================
echo   Setup selesai.
echo   Jalankan run.bat untuk membuka aplikasi.
echo   Log lengkap: %LOGFILE%
echo ============================================================

:end
echo.
echo --------------------------------------------------------------
echo Jendela ini TIDAK akan tertutup otomatis.
echo Tekan tombol apa saja untuk menutup setelah membaca pesan.
echo Kalau ada error, lampirkan setup.log saat melapor balik.
echo --------------------------------------------------------------
pause >nul
endlocal
