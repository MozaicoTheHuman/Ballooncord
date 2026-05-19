@echo off
title mish

rmdir /s /q build
rmdir /s /q dist
del /q *.spec

pyinstaller --onefile --windowed discord_balloon.py
echo.
echo =========================
echo ta listo mi loco
echo =========================
pause