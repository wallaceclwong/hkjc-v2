@echo off
REM Automated Racecard Fetching - Windows Task Scheduler Setup
REM This batch file can be scheduled to run daily

cd /d C:\Users\ASUS\hkjc
.venv\Scripts\python.exe auto_fetch_racecards.py

REM Log the run
echo %date% %time% - Auto fetch completed >> logs\auto_fetch.log
