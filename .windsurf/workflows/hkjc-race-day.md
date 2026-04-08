---
description: HKJC race day workflow — full automated pipeline from racecard to bets
---

## Race Day Workflow

### Step 1: Check mempalace for latest system state
Call `mempalace_kg_query(entity="HKJC betting system")` to confirm thresholds and bankroll settings before running.

### Step 2: Fetch racecards (run from PC)
```
python scripts/pc_race_day.py
```
This scrapes racecards via residential IP, SCPs to VM, triggers vm_predict.py on VM.

### Step 3: Generate predictions (if running locally)
```
python auto_full_workflow.py <YYYY-MM-DD> <ST|HV>
```

### Step 4: Review high-confidence bets
Check `data\high_confidence_bets_<date>_<track>.json` or visit https://hkjc-v2.web.app

### Step 5: Monitor live odds
Market watchdog freezes bets if odds move > 30%. Shadow model must agree within 10%.

### Step 6: After races — auto-learn
```
python auto_fetch_and_learn.py <YYYY-MM-DD> <ST|HV>
```

### Step 7: Update mempalace after session
Call `mempalace_diary_write` with race day results summary in AAAK format.
If bankroll or thresholds changed, call `mempalace_kg_invalidate` + `mempalace_kg_add`.
