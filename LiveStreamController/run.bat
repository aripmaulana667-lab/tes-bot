@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Virtual environment belum dibuat.
    echo Jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" controller_app.py
endlocal
