@echo off
REM Automated Full Workflow - Windows Task Scheduler
REM Fetches racecards, syncs to VM, triggers AI predictions
REM Cost: ~$0.22 per race day

cd /d C:\Users\ASUS\hkjc
.venv\Scripts\python.exe scripts\pc_race_day.py

REM Log the run
echo %date% %time% - Race day workflow completed >> logs\auto_workflow.log
