# Manual Task Scheduler Setup (5 minutes)

The automated scripts need Administrator privileges. Here's the simplest manual method:

---

## Quick Setup (Copy-Paste Method)

### Step 1: Open Command Prompt as Administrator

1. Press `Win + X`
2. Click "Terminal (Admin)" or "Command Prompt (Admin)"
3. Click "Yes" on the UAC prompt

### Step 2: Copy and Paste These Commands

**Task 1: Auto Fetch Racecards**
```cmd
schtasks /create /tn "HKJC Auto Fetch Racecards" /tr "C:\Users\ASUS\hkjc\setup_auto_fetch.bat" /sc weekly /d TUE,SAT,SUN /st 22:00 /rl HIGHEST /f
```

**Task 2: Auto Predictions**
```cmd
schtasks /create /tn "HKJC Auto Predictions" /tr "C:\Users\ASUS\hkjc\setup_auto_predictions.bat" /sc weekly /d WED,SAT,SUN /st 06:00 /rl HIGHEST /f
```

**Task 3: Auto Learning**
```cmd
schtasks /create /tn "HKJC Auto Learning" /tr "C:\Users\ASUS\hkjc\.venv\Scripts\python.exe auto_fetch_and_learn.py auto auto" /sc weekly /d WED,SAT,SUN /st 23:00 /rl HIGHEST /f
```

### Step 3: Verify

Open Task Scheduler to verify:
```cmd
taskschd.msc
```

You should see 3 tasks created.

---

## Alternative: Use Task Scheduler GUI (10 minutes)

If commands don't work, follow the detailed guide in `TASK_SCHEDULER_SETUP.md`

---

## What These Tasks Do

**Task 1** (Tue/Sat/Sun 10 PM):
- Fetches racecards automatically
- FREE

**Task 2** (Wed/Sat/Sun 6 AM):
- Generates predictions
- Costs $0.22 per race day

**Task 3** (Wed/Sat/Sun 11 PM):
- Fetches results and runs auto-learning
- FREE

---

## After Setup

Your system will be **95% automated**:
- Wake up Wednesday 7 AM
- Review bet list (10 min)
- Place bets
- Done!

Everything else happens automatically! 🚀
