@echo off
REM Create Task 2: Auto Generate Predictions

schtasks /create /tn "HKJC Auto Predictions" /tr "C:\Users\ASUS\hkjc\setup_auto_predictions.bat" /sc weekly /d WED,SAT,SUN /st 06:00 /ru "%USERNAME%" /rl HIGHEST /f

echo Task 2 created: HKJC Auto Predictions
echo Schedule: Wednesday/Saturday/Sunday 6 AM
pause
