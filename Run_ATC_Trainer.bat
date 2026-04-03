@echo off
title ATC Training System
echo Starting ATC Training System...
echo Make sure Microsoft Flight Simulator X (FSX) is already running!
echo -------------------------------------------------------------

cd /d "d:\FlightSim"
python main.py

echo.
echo -------------------------------------------------------------
echo Session ended. Press any key to close this window.
pause >nul
