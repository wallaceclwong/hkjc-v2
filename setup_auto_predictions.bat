@echo off
REM Automated Full Workflow - Windows Task Scheduler
REM Fetches racecards, generates predictions, filters high confidence
REM Cost: ~$0.22 per run

cd /d C:\Users\ASUS\hkjc
.venv\Scripts\python.exe auto_full_workflow.py

REM Log the run
echo %date% %time% - Auto workflow completed >> logs\auto_workflow.log
