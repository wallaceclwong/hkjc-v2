# Windows Task Scheduler Setup Guide

## Quick Setup (5 minutes)

Follow these steps to automate your betting system:

---

## Task 1: Auto Fetch Racecards (Tuesday/Saturday/Sunday 10 PM)

### Step-by-Step:

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create Task**
   - Click "Create Task" (not "Create Basic Task")
   - Name: `HKJC Auto Fetch Racecards`
   - Description: `Automatically fetch racecards for upcoming races`
   - Check: ☑ Run whether user is logged on or not
   - Check: ☑ Run with highest privileges

3. **Triggers Tab**
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Weekly`
   - Check: ☑ Tuesday, ☑ Saturday, ☑ Sunday
   - Start: `10:00:00 PM`
   - Click OK

4. **Actions Tab**
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `C:\Users\ASUS\hkjc\setup_auto_fetch.bat`
   - Start in: `C:\Users\ASUS\hkjc`
   - Click OK

5. **Conditions Tab**
   - Uncheck: ☐ Start the task only if the computer is on AC power
   - Check: ☑ Wake the computer to run this task

6. **Settings Tab**
   - Check: ☑ Allow task to be run on demand
   - Check: ☑ Run task as soon as possible after a scheduled start is missed
   - If the task fails, restart every: `1 hour`
   - Attempt to restart up to: `3 times`

7. **Save**
   - Click OK
   - Enter your Windows password if prompted

---

## Task 2: Auto Generate Predictions (Wednesday/Saturday/Sunday 6 AM)

### Step-by-Step:

1. **Create Task**
   - Name: `HKJC Auto Predictions`
   - Description: `Generate predictions for race day`
   - Check: ☑ Run whether user is logged on or not
   - Check: ☑ Run with highest privileges

2. **Triggers Tab**
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Weekly`
   - Check: ☑ Wednesday, ☑ Saturday, ☑ Sunday
   - Start: `6:00:00 AM`
   - Click OK

3. **Actions Tab**
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `C:\Users\ASUS\hkjc\setup_auto_predictions.bat`
   - Start in: `C:\Users\ASUS\hkjc`
   - Click OK

4. **Conditions Tab**
   - Uncheck: ☐ Start the task only if the computer is on AC power
   - Check: ☑ Wake the computer to run this task

5. **Settings Tab**
   - Same as Task 1

6. **Save**
   - Click OK
   - Enter password if prompted

---

## Task 3: Auto Learning (Wednesday/Saturday/Sunday 11 PM)

### Step-by-Step:

1. **Create Task**
   - Name: `HKJC Auto Learning`
   - Description: `Fetch results and run auto-learning`
   - Check: ☑ Run whether user is logged on or not
   - Check: ☑ Run with highest privileges

2. **Triggers Tab**
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Weekly`
   - Check: ☑ Wednesday, ☑ Saturday, ☑ Sunday
   - Start: `11:00:00 PM`
   - Click OK

3. **Actions Tab**
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `C:\Users\ASUS\hkjc\.venv\Scripts\python.exe`
   - Add arguments: `auto_fetch_and_learn.py auto auto`
   - Start in: `C:\Users\ASUS\hkjc`
   - Click OK

4. **Conditions Tab**
   - Same as Task 1

5. **Settings Tab**
   - Same as Task 1

6. **Save**
   - Click OK

---

## Verify Setup

### Check Tasks are Created:
1. Open Task Scheduler
2. Click "Task Scheduler Library"
3. You should see:
   - ✅ HKJC Auto Fetch Racecards
   - ✅ HKJC Auto Predictions
   - ✅ HKJC Auto Learning

### Test a Task:
1. Right-click on "HKJC Auto Fetch Racecards"
2. Click "Run"
3. Check if it runs successfully
4. Check log: `type logs\auto_fetch.log`

---

## Your Automated Schedule

### **Tuesday 10 PM** (Automatic)
- Fetches racecards for Wednesday
- PC wakes up, runs script, goes back to sleep

### **Wednesday 6 AM** (Automatic)
- Generates predictions ($0.22)
- Filters high confidence bets
- Saves bet list

### **Wednesday 7 AM** (Manual - 10 min)
- You wake up
- Open: `data\high_confidence_bets_2026-04-01_ST.json`
- Review bets
- Place bets on HKJC

### **Wednesday 11 PM** (Automatic)
- Fetches results
- Runs auto-learning
- Updates model

### **Saturday/Sunday** (Same schedule)
- Repeat for weekend races

---

## Troubleshooting

### Task doesn't run?
- Check Task Scheduler History (View → Show History)
- Make sure PC is on or set to wake
- Check Windows password is correct

### Task runs but fails?
- Check logs: `type logs\auto_fetch.log`
- Check logs: `type logs\auto_workflow.log`
- Run batch file manually to see errors

### PC doesn't wake up?
- BIOS settings: Enable "Wake on RTC"
- Power Options: Allow wake timers
- Check "Wake the computer to run this task" is checked

---

## Monitoring

### Check if automation is working:
```bash
# View logs
type logs\auto_fetch.log
type logs\auto_workflow.log

# Check latest files
dir data\racecard_*.json /O:D
dir data\predictions\prediction_*.json /O:D
dir data\high_confidence_bets_*.json /O:D
```

### View Task History:
1. Open Task Scheduler
2. Click on a task
3. Click "History" tab
4. See all runs and results

---

## Cost Reminder

- **Racecard fetching**: FREE
- **Predictions**: $0.22 per race day
- **Auto-learning**: FREE
- **Total**: ~$2/month (8-10 race days)

---

## What Happens Now

**You do nothing!**

The system will:
- ✅ Fetch racecards automatically
- ✅ Generate predictions automatically
- ✅ Filter high confidence bets automatically
- ✅ Learn from results automatically

**You only**:
- Wake up Wednesday 7 AM
- Review bet list (10 min)
- Place bets

**That's it!** 🎯

---

## Summary

**Time to set up**: 10 minutes
**Time saved per race day**: 15 minutes
**Automation level**: 95%

Your betting system is now fully automated! 🚀
