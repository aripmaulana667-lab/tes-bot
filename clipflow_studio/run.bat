@echo off
title ClipFlow Studio

if not exist venv (
    echo Virtual environment belum ditemukan.
    echo Jalankan setup.bat terlebih dahulu.
    pause
    exit /b
)

call venv\Scripts\activate
python run.py

if errorlevel 1 (
    echo.
    echo Aplikasi berhenti karena error.
    pause
)
