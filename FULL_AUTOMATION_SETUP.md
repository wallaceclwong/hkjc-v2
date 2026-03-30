# Full Automation Setup Guide

## What's Automated

Your betting system is now **fully automated** at only **$0.22 per race day** (~$2/month):

✅ **Racecard fetching** - Automatic
✅ **Prediction generation** - Automatic ($0.22)
✅ **High confidence filtering** - Automatic
✅ **Results fetching** - Automatic
✅ **Auto-learning** - Automatic

**You only**: Review bets and place them manually

---

## Setup Windows Task Scheduler

### Task 1: Auto Workflow (Predictions)

**When**: Wednesday 6:00 AM (or your preferred time)

**Steps**:
1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Click "Create Basic Task"
3. Name: "HKJC Auto Predictions"
4. Trigger: Weekly, Wednesday, 6:00 AM
5. Action: Start a program
   - Program: `C:\Users\ASUS\hkjc\setup_auto_predictions.bat`
   - Start in: `C:\Users\ASUS\hkjc`
6. Settings:
   - ✅ Wake computer to run
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges

### Task 2: Post-Race Learning

**When**: Wednesday 11:00 PM (after races)

**Steps**:
1. Create another task: "HKJC Auto Learning"
2. Trigger: Weekly, Wednesday, 11:00 PM
3. Action: Start a program
   - Program: `C:\Users\ASUS\hkjc\.venv\Scripts\python.exe`
   - Arguments: `auto_fetch_and_learn.py auto auto`
   - Start in: `C:\Users\ASUS\hkjc`

---

## Your Fully Automated Workflow

### **Tuesday 10 PM** (Automatic)
- Task Scheduler wakes PC
- Fetches racecards for Wednesday
- PC goes back to sleep
- **You: Sleep** 😴

### **Wednesday 6 AM** (Automatic)
- Task Scheduler wakes PC
- Generates predictions ($0.22)
- Filters high confidence bets
- Saves bet list to file
- PC stays on
- **You: Still sleeping** 😴

### **Wednesday 7 AM** (Manual - 10 minutes)
- Wake up
- Open: `data/high_confidence_bets_2026-04-01_ST.json`
- Review 2-4 recommended bets
- Log into HKJC
- Place bets
- **Done for the day!**

### **Wednesday 11 PM** (Automatic)
- Task Scheduler runs
- Fetches results
- Runs auto-learning
- Updates model
- **You: Don't even know it happened** 😴

---

## Manual Alternative (No Task Scheduler)

If you don't want to set up Task Scheduler, just run this **one command** Wednesday morning:

```bash
python auto_full_workflow.py
```

This does everything:
- Checks for racecards (fetches if needed)
- Generates predictions ($0.22)
- Filters high confidence
- Shows bet recommendations

**Time**: 15 minutes
**Cost**: $0.22

---

## Testing the Automation

**Test it now** (won't charge, no racecards available):
```bash
python auto_full_workflow.py 2026-04-01 ST
```

You'll see:
- Checks for racecards
- Would generate predictions (but no racecards yet)
- Shows what would happen

---

## Cost Breakdown

### Per Race Day
- Predictions: $0.22
- Everything else: FREE

### Per Month (8 race days)
- Total: ~$1.76
- Less than a coffee! ☕

### Per Year
- Total: ~$26
- Negligible for a betting system

---

## What You Control

**Automated** (happens without you):
- ✅ Racecard fetching
- ✅ Prediction generation
- ✅ High confidence filtering
- ✅ Results fetching
- ✅ Auto-learning

**Manual** (you decide):
- ❌ Reviewing bets
- ❌ Placing bets
- ❌ Bet sizing

**This is perfect** - automation handles the work, you control the money! 💰

---

## Monitoring

**Check if automation is working**:
```bash
# View workflow log
type logs\auto_workflow.log

# Check latest predictions
dir data\predictions\prediction_*.json /O:D

# Check latest bets
dir data\high_confidence_bets_*.json /O:D
```

**If something fails**:
- Check Task Scheduler history
- Check `logs/auto_workflow.log`
- PC must be on (or set to wake)

---

## Recommendation

**Week 1**: Run manually to learn
```bash
python auto_full_workflow.py 2026-04-01 ST
```

**Week 2+**: Set up Task Scheduler for full automation

Start manual, automate when comfortable! 🎯

---

## Summary

**Time commitment**: 10 minutes per race day (just place bets)
**Cost**: $0.22 per race day (~$2/month)
**Automation level**: 95%

Everything is automated except the final decision to place bets - exactly as it should be! 🚀
