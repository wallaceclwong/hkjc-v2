# PowerShell Script to Set Up Task Scheduler Tasks
# Run this as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HKJC Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current user
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "Setting up tasks for user: $currentUser" -ForegroundColor Yellow
Write-Host ""

# Task 1: Auto Fetch Racecards (Tuesday/Saturday/Sunday 10 PM)
Write-Host "Creating Task 1: Auto Fetch Racecards..." -ForegroundColor Green

$action1 = New-ScheduledTaskAction -Execute "C:\Users\ASUS\hkjc\setup_auto_fetch.bat" -WorkingDirectory "C:\Users\ASUS\hkjc"

$trigger1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday,Saturday,Sunday -At 10:00PM

$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Hours 1)

$principal1 = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "HKJC Auto Fetch Racecards" -Action $action1 -Trigger $trigger1 -Settings $settings1 -Principal $principal1 -Description "Automatically fetch racecards for upcoming races" -Force

Write-Host "[OK] Task 1 created successfully" -ForegroundColor Green
Write-Host ""

# Task 2: Auto Generate Predictions (Wednesday/Saturday/Sunday 6 AM)
Write-Host "Creating Task 2: Auto Generate Predictions..." -ForegroundColor Green

$action2 = New-ScheduledTaskAction -Execute "C:\Users\ASUS\hkjc\setup_auto_predictions.bat" -WorkingDirectory "C:\Users\ASUS\hkjc"

$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday,Saturday,Sunday -At 6:00AM

$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Hours 1)

$principal2 = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "HKJC Auto Predictions" -Action $action2 -Trigger $trigger2 -Settings $settings2 -Principal $principal2 -Description "Generate predictions for race day (costs ~$0.22)" -Force

Write-Host "[OK] Task 2 created successfully" -ForegroundColor Green
Write-Host ""

# Task 3: Auto Learning (Wednesday/Saturday/Sunday 11 PM)
Write-Host "Creating Task 3: Auto Learning..." -ForegroundColor Green

$action3 = New-ScheduledTaskAction -Execute "C:\Users\ASUS\hkjc\.venv\Scripts\python.exe" -Argument "auto_fetch_and_learn.py auto auto" -WorkingDirectory "C:\Users\ASUS\hkjc"

$trigger3 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday,Saturday,Sunday -At 11:00PM

$settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Hours 1)

$principal3 = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "HKJC Auto Learning" -Action $action3 -Trigger $trigger3 -Settings $settings3 -Principal $principal3 -Description "Fetch results and run auto-learning" -Force

Write-Host "[OK] Task 3 created successfully" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Created 3 scheduled tasks:" -ForegroundColor Yellow
Write-Host "  1. HKJC Auto Fetch Racecards (Tue/Sat/Sun 10 PM)" -ForegroundColor White
Write-Host "  2. HKJC Auto Predictions (Wed/Sat/Sun 6 AM)" -ForegroundColor White
Write-Host "  3. HKJC Auto Learning (Wed/Sat/Sun 11 PM)" -ForegroundColor White
Write-Host ""
Write-Host "To verify, open Task Scheduler and check 'Task Scheduler Library'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your system is now 95% automated!" -ForegroundColor Green
Write-Host ""
