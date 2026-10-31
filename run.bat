@echo off
title AutoCast Launcher
cd /d "%~dp0"
echo Memulai AutoCast Studio...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ada masalah saat menjalankan AutoCast.
    pause
)
