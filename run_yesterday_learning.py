import glob
import os
from services.auto_learning import trigger_auto_learning_for_race

# Find all races from yesterday
result_files = glob.glob("c:/Users/ASUS/hkjc/data/results/results_2026-03-29_*.json")

print(f"Running auto-learning for {len(result_files)} races from March 29:")

for f in sorted(result_files):
    # Extract race_id from filename
    race_id = os.path.basename(f).replace("results_", "").replace(".json", "")
    print(f"\nProcessing {race_id}...")
    trigger_auto_learning_for_race(race_id.replace("2026-03-29", "20260329"))

print("\n✅ Auto-learning complete for all races!")
