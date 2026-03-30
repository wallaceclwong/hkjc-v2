# Setup Automated Racecard Fetching

## Option 1: Manual Run (Recommended to Start)

Just run this command anytime:
```bash
python auto_fetch_racecards.py
```

It will:
- Check next 7 days for race dates (Wed, Sat, Sun)
- Try to fetch racecards for ST and HV
- Skip if already downloaded
- Show what's available

**Run this Tuesday night or Wednesday morning** before generating predictions.

---

## Option 2: Windows Task Scheduler (Fully Automated)

### Setup Steps

**1. Open Task Scheduler**
- Press `Win + R`
- Type `taskschd.msc`
- Press Enter

**2. Create New Task**
- Click "Create Basic Task"
- Name: "HKJC Racecard Auto-Fetch"
- Description: "Automatically fetch racecards for upcoming races"

**3. Set Trigger**
- When: Daily
- Start: 10:00 PM (22:00)
- Recur every: 1 day

**4. Set Action**
- Action: Start a program
- Program/script: `C:\Users\ASUS\hkjc\setup_auto_fetch.bat`
- Start in: `C:\Users\ASUS\hkjc`

**5. Conditions**
- Uncheck "Start only if on AC power" (if laptop)
- Check "Wake computer to run this task"

**6. Settings**
- Check "Run task as soon as possible after scheduled start is missed"
- Check "If task fails, restart every: 1 hour"

**7. Save**
- Enter your Windows password if prompted

---

## What Happens Automatically

**Every night at 10 PM**:
1. Script runs automatically
2. Checks if racecards available for next 7 days
3. Downloads any new racecards
4. Logs results to `logs/auto_fetch.log`

**You wake up Wednesday morning**:
- Racecards already downloaded
- Ready to generate predictions immediately
- No manual fetching needed

---

## Your New Workflow (Fully Automated Racecards)

### **Tuesday Night** (Automatic)
- 10 PM: Task Scheduler runs
- Racecards fetched automatically
- You do nothing!

### **Wednesday Morning** (~25 min, $2.20)
```bash
# 1. Generate predictions (racecards already there!)
python batch_predict.py 2026-04-01 ST 11

# 2. Filter high confidence
python filter_high_confidence.py 2026-04-01 ST

# 3. Place bets manually
```

### **Wednesday Evening** (~5 min, FREE)
```bash
# Automated learning
python auto_fetch_and_learn.py 2026-04-01 ST
```

---

## Benefits of Automation

✅ **Never miss racecards** - Fetches automatically
✅ **Wake up ready** - Racecards waiting for you
✅ **No manual checking** - Script handles it
✅ **Saves 5 minutes** - One less step Wednesday morning
✅ **PC can be asleep** - Task Scheduler wakes it

---

## Monitoring

**Check if it's working**:
```bash
# View log
type logs\auto_fetch.log

# Check last run
dir data\racecard_*.json /O:D
```

**If it's not working**:
- Check Task Scheduler history
- Make sure PC is on at 10 PM (or set to wake)
- Check `logs/auto_fetch.log` for errors

---

## Recommendation

**Week 1**: Run manually to understand the process
```bash
python auto_fetch_racecards.py
```

**Week 2+**: Set up Task Scheduler for full automation

This way you learn the system first, then automate when comfortable! 🎯
