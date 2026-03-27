@echo off
echo ========================================
echo   HKJC Dashboard Frontend Sync
echo ========================================
echo.
echo This will sync the latest dashboard files to Firebase.
echo.
cd /d "%~dp0"
call npx firebase deploy --only hosting --project hkjc-v2
echo.
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed! 
    echo Please make sure you are logged in by running: npx firebase login
) else (
    echo [SUCCESS] Dashboard updated!
)
echo.
pause
