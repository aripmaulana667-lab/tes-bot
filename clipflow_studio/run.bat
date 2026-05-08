@echo off
setlocal
title ClipFlow Studio

REM Always run from the directory that contains this script.
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo Virtual environment belum lengkap di folder venv\.
    echo Jalankan setup.bat terlebih dahulu.
    goto :end
)

set "VENVPY=%~dp0venv\Scripts\python.exe"

echo Memulai ClipFlow Studio...
"%VENVPY%" run.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo Aplikasi berhenti dengan kode error %RC%.
    echo Cek logs\clipflow.log untuk detail.
)

:end
echo.
echo --------------------------------------------------------------
echo Tekan tombol apa saja untuk menutup jendela ini.
echo --------------------------------------------------------------
pause >nul
endlocal
