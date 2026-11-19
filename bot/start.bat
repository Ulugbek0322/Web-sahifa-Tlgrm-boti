@echo off
chcp 65001 >nul
title Deutsch Mentor bot
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python topilmadi. python.org saytidan Python 3 ni örnating va "Add python.exe to PATH" belgisini qöying.
  pause
  exit /b 1
)
python bot.py
pause
