@echo off
echo Rescheduling HKJC Auto Predictions from 6 AM to 10 AM...
echo.

REM Delete old task
schtasks /delete /tn "HKJC Auto Predictions" /f

REM Create new task with 10 AM schedule
schtasks /create /tn "HKJC Auto Predictions" /tr "C:\Users\ASUS\hkjc\setup_auto_predictions.bat" /sc weekly /d WED,SAT,SUN /st 10:00 /rl HIGHEST /f

echo.
echo Task rescheduled to 10:00 AM (Wednesday/Saturday/Sunday)
echo.
pause
