@echo off
REM Automated Racecard Fetching - Windows Task Scheduler Setup
REM This batch file can be scheduled to run daily

cd /d C:\Users\ASUS\hkjc
.venv\Scripts\python.exe auto_fetch_racecards.py

REM If racecards fetched, also trigger full workflow with VM sync
if %errorlevel% equ 0 (
    echo %date% %time% - Racecards fetched, triggering full workflow >> logs\auto_fetch.log
    .venv\Scripts\python.exe scripts\pc_race_day.py
) else (
    echo %date% %time% - Auto fetch completed (no new racecards) >> logs\auto_fetch.log
)
