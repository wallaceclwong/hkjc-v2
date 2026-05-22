# PC Uptime Requirements Analysis

## What Needs Your PC Running

### ❌ **Does NOT Need PC On**

1. **Firestore Data Storage**
   - Results stored in cloud
   - Predictions stored in cloud
   - Accessible anytime from anywhere
   - **PC can be off**

2. **Racecard Publishing**
   - HKJC publishes racecards on their schedule
   - Happens whether your PC is on or not
   - **PC can be off**

3. **Race Results**
   - Races happen regardless
   - Results published by HKJC
   - **PC can be off**

### ✅ **NEEDS PC On**

1. **Fetching Racecards** (Manual)
   - Run: `smart_racecard_fetcher.py`
   - Takes: ~5 minutes
   - When: Tuesday night or Wednesday morning
   - **PC must be on for 5 minutes**

2. **Generating Predictions** (Manual, Costs Money)
   - Run: `prediction_engine.py`
   - Takes: ~10-15 minutes for 11 races
   - When: After racecards fetched
   - Uses: DeepSeek AI (billable)
   - **PC must be on for 15 minutes**

3. **Placing Bets** (Manual)
   - You decide which bets to place
   - Log into HKJC betting site
   - When: Before races start
   - **PC must be on while you bet**

4. **Fetching Results** (Manual)
   - Run: `results_ingest.py`
   - Takes: ~5 minutes
   - When: After races finish
   - **PC must be on for 5 minutes**

5. **Running Auto-Learning** (Manual)
   - Run: `run_full_auto_learning.py`
   - Takes: ~3 minutes
   - When: After results fetched
   - **PC must be on for 3 minutes**

6. **Dashboard** (Optional)
   - Run: `dashboard/server.py`
   - Only if you want to view it
   - **PC must be on while viewing**

---

## Total PC Uptime Needed

### **Per Race Day** (e.g., Wednesday)

**Before Races**:
- Fetch racecards: 5 min
- Generate predictions: 15 min
- Review & place bets: 30 min
- **Total: ~50 minutes**

**After Races**:
- Fetch results: 5 min
- Run auto-learning: 3 min
- **Total: ~8 minutes**

**Grand Total: ~1 hour per race day**

### **Per Week**
- 2 race days (Wed, Sun typically)
- **Total: ~2 hours/week**

### **Per Month**
- ~8-10 race days
- **Total: ~8-10 hours/month**

---

## Current Setup: Fully Manual

**Everything requires you to**:
1. Turn on PC
2. Run script
3. Wait for completion
4. Turn off PC (if desired)

**No automation currently running**

---

## Could Be Automated (Would Need PC On 24/7)

### **With Cloud Functions** ($1-2/month)
- Auto-fetch racecards when published
- Auto-run predictions
- Send notifications to phone
- **PC can stay off**

### **With Scheduled Tasks** (Free, but PC must be on)
- Windows Task Scheduler
- Auto-run scripts at specific times
- **PC must be on at scheduled times**

---

## My Assessment

### **Current Reality**

You need PC on for:
- **~1 hour per race day**
- **~8-10 hours per month**
- **All manual operations**

### **The Rest of the Time**

Your PC can be:
- ✅ Off
- ✅ Sleeping
- ✅ Doing other things

**Data is safe in Firestore even when PC is off**

---

## Recommendation

**Keep current manual setup** because:
1. Only ~1 hour per race day needed
2. You want control over predictions (they cost money)
3. You want control over bets
4. More secure (not running 24/7)
5. Lower electricity cost

**Don't automate** unless:
- You want hands-off operation
- You're willing to pay for Cloud Functions
- You trust the system to bet without you

---

## Bottom Line

**Your PC needs to be on for ~1 hour per race day, that's it.**

The other 167 hours of the week, it can be off! 🎯
