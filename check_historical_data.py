import glob
import json
from collections import Counter
from datetime import datetime

print("="*60)
print("HISTORICAL DATA ANALYSIS")
print("="*60)

# Check predictions
pred_files = glob.glob("data/predictions/*.json")
print(f"\nTotal prediction files: {len(pred_files)}")

# Analyze dates
dates = []
venues = []
races_by_date = Counter()

for f in pred_files:
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            data = json.load(file)
            race_id = data.get('race_id', '')
            if race_id:
                parts = race_id.split('_')
                if len(parts) >= 2:
                    date = parts[0]
                    venue = parts[1] if len(parts) > 1 else 'Unknown'
                    dates.append(date)
                    venues.append(venue)
                    races_by_date[date] += 1
    except:
        continue

if dates:
    print(f"Unique race dates: {len(set(dates))}")
    print(f"Date range: {min(dates)} to {max(dates)}")
    
    # Count by venue
    venue_counts = Counter(venues)
    print(f"\nBy venue:")
    for venue, count in venue_counts.most_common():
        print(f"  {venue}: {count} races")
    
    # Show top 10 dates
    print(f"\nTop 10 race dates:")
    for date, count in races_by_date.most_common(10):
        print(f"  {date}: {count} races")

# Check results
result_files = glob.glob("data/results/*.json")
print(f"\n{'='*60}")
print(f"Total result files: {len(result_files)}")

result_dates = []
for f in result_files:
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            data = json.load(file)
            race_id = data.get('race_id', '')
            if race_id:
                date = race_id.split('_')[0]
                result_dates.append(date)
    except:
        continue

if result_dates:
    print(f"Unique result dates: {len(set(result_dates))}")
    print(f"Date range: {min(result_dates)} to {max(result_dates)}")

# Check racecards
racecard_files = glob.glob("data/racecard_*.json")
print(f"\n{'='*60}")
print(f"Total racecard files: {len(racecard_files)}")

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print("="*60)
print(f"Predictions: {len(pred_files)} races across {len(set(dates))} days")
print(f"Results: {len(result_files)} races")
print(f"Racecards: {len(racecard_files)} races")

# Calculate if we have enough for training
if len(pred_files) >= 1000:
    print(f"\n[OK] You have {len(pred_files)} predictions - PLENTY for training!")
else:
    print(f"\n[WARN] You have {len(pred_files)} predictions - could use more")
    print(f"       Recommended: 1000+ races")
    print(f"       Need: {1000 - len(pred_files)} more races")

print("="*60)
