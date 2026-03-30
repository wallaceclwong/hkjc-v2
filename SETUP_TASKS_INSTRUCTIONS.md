# Task Scheduler Setup - Simple Method

The automated script needs Administrator privileges. Here's the easiest way to set it up:

---

## Method 1: Run PowerShell as Administrator (Recommended)

1. **Right-click on Windows Start button**
2. **Select "Windows PowerShell (Admin)"** or "Terminal (Admin)"
3. **Navigate to folder**:
   ```powershell
   cd C:\Users\ASUS\hkjc
   ```
4. **Run setup script**:
   ```powershell
   .\setup_task_scheduler.ps1
   ```
5. **Done!** All 3 tasks will be created automatically

---

## Method 2: Manual Setup (10 minutes)

If you prefer manual setup, follow `TASK_SCHEDULER_SETUP.md` for detailed step-by-step instructions.

---

## Verify Tasks Were Created

1. Press `Win + R`
2. Type: `taskschd.msc`
3. Press Enter
4. Look for these tasks:
   - ✅ HKJC Auto Fetch Racecards
   - ✅ HKJC Auto Predictions
   - ✅ HKJC Auto Learning

---

## Test a Task

1. Right-click on "HKJC Auto Fetch Racecards"
2. Click "Run"
3. Check if it completes successfully
4. View log: `type logs\auto_fetch.log`

---

## Your Automated Schedule

Once set up:

- **Tuesday 10 PM**: Fetch racecards (automatic)
- **Wednesday 6 AM**: Generate predictions (automatic, $0.22)
- **Wednesday 7 AM**: You review and place bets (10 min)
- **Wednesday 11 PM**: Auto-learning (automatic)

**Total automation: 95%**

---

## Next Step

Run PowerShell as Administrator and execute the setup script! 🚀
