@echo off
title Music Spectrum Lyric Video Maker

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

python -m app.main
set RC=%ERRORLEVEL%

if not "%RC%"=="0" (
    echo.
    echo The application exited with error code %RC%.
    echo Read the messages above for details. The window will stay open.
    pause
    exit /b %RC%
)

exit /b 0
