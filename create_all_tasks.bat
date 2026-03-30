@echo off
echo ========================================
echo HKJC Task Scheduler Setup
echo ========================================
echo.
echo Creating 3 automated tasks...
echo.

REM Task 1: Auto Fetch Racecards (Tue/Sat/Sun 10 PM)
echo [1/3] Creating Auto Fetch Racecards task...
schtasks /create /tn "HKJC Auto Fetch Racecards" /tr "C:\Users\ASUS\hkjc\setup_auto_fetch.bat" /sc weekly /d TUE,SAT,SUN /st 22:00 /ru "%USERNAME%" /rl HIGHEST /f
if %errorlevel% equ 0 (
    echo [OK] Task 1 created successfully
) else (
    echo [ERROR] Task 1 failed
)
echo.

REM Task 2: Auto Generate Predictions (Wed/Sat/Sun 6 AM)
echo [2/3] Creating Auto Predictions task...
schtasks /create /tn "HKJC Auto Predictions" /tr "C:\Users\ASUS\hkjc\setup_auto_predictions.bat" /sc weekly /d WED,SAT,SUN /st 06:00 /ru "%USERNAME%" /rl HIGHEST /f
if %errorlevel% equ 0 (
    echo [OK] Task 2 created successfully
) else (
    echo [ERROR] Task 2 failed
)
echo.

REM Task 3: Auto Learning (Wed/Sat/Sun 11 PM)
echo [3/3] Creating Auto Learning task...
schtasks /create /tn "HKJC Auto Learning" /tr "C:\Users\ASUS\hkjc\.venv\Scripts\python.exe auto_fetch_and_learn.py auto auto" /sc weekly /d WED,SAT,SUN /st 23:00 /ru "%USERNAME%" /rl HIGHEST /f
if %errorlevel% equ 0 (
    echo [OK] Task 3 created successfully
) else (
    echo [ERROR] Task 3 failed
)
echo.

echo ========================================
echo SETUP COMPLETE
echo ========================================
echo.
echo Created tasks:
echo   1. HKJC Auto Fetch Racecards (Tue/Sat/Sun 10 PM)
echo   2. HKJC Auto Predictions (Wed/Sat/Sun 6 AM)
echo   3. HKJC Auto Learning (Wed/Sat/Sun 11 PM)
echo.
echo To verify: Open Task Scheduler (taskschd.msc)
echo.
echo Your system is now 95%% automated!
echo.
pause
