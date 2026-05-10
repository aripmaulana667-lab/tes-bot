@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment belum dibuat.
    echo Jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)

echo ============================================================
echo  LiveStream Server - Starting...
echo  (tutup jendela ini untuk stop server)
echo ============================================================

".venv\Scripts\python.exe" server_app.py

echo.
echo Server berhenti.
pause
endlocal
