@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set LOCAL_MODE=true
title DiCoCon Bot (Local Mode)
cd /d "%~dp0"

".venv\Scripts\python.exe" bot.py

echo.
pause
