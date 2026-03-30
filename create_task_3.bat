@echo off
REM Create Task 3: Auto Learning

schtasks /create /tn "HKJC Auto Learning" /tr "C:\Users\ASUS\hkjc\.venv\Scripts\python.exe auto_fetch_and_learn.py auto auto" /sc weekly /d WED,SAT,SUN /st 23:00 /ru "%USERNAME%" /rl HIGHEST /f

echo Task 3 created: HKJC Auto Learning
echo Schedule: Wednesday/Saturday/Sunday 11 PM
pause
