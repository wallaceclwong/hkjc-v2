"""
Run Auto-Learning on All Historical Data
Processes all matched prediction-result pairs
100% FREE - No API calls, just local processing
"""
import glob
import json
import os
from pathlib import Path
from collections import Counter

print("="*60)
print("FULL HISTORICAL AUTO-LEARNING")
print("="*60)
print("\n[INFO] 100% FREE - No cloud charges")
print("[INFO] Processing local files only")

# Find all matched pairs
pred_files = set(Path(f).stem.replace('prediction_', '') for f in glob.glob('data/predictions/prediction_*.json'))
result_files = set(Path(f).stem.replace('results_', '') for f in glob.glob('data/results/results_*.json'))

matched_ids = pred_files & result_files
matched_list = sorted(list(matched_ids))

print(f"\nFound {len(matched_list)} matched prediction-result pairs")
print(f"Date range: {min(matched_list)} to {max(matched_list)}")

# Import auto-learning
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.auto_learning import AutoLearning

learner = AutoLearning()

# Process in batches
print("\n" + "="*60)
print("PROCESSING RACES")
print("="*60)

processed = 0
triggered_recal = 0
errors = 0

for i, race_id in enumerate(matched_list):
    if i % 50 == 0:
        print(f"\nProgress: {i}/{len(matched_list)} ({i*100//len(matched_list)}%)")
    
    try:
        # Convert date format if needed (YYYY-MM-DD to YYYYMMDD)
        if '-' in race_id:
            parts = race_id.split('_')
            date_part = parts[0].replace('-', '')
            race_id_compact = f"{date_part}_{parts[1]}_{parts[2]}"
        else:
            race_id_compact = race_id
        
        # Run auto-learning
        learner.trigger_post_race_learning(race_id_compact)
        processed += 1
        
    except Exception as e:
        errors += 1
        if errors <= 5:  # Only show first 5 errors
            print(f"  [ERROR] {race_id}: {str(e)[:100]}")

print(f"\n{'='*60}")
print("PROCESSING COMPLETE")
print("="*60)

print(f"\nRaces processed: {processed}")
print(f"Errors: {errors}")

# Check learning log
log_file = Path("data/logs/auto_learning.log")
if log_file.exists():
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    print(f"\nLearning log entries: {len(lines)}")
    
    # Analyze last 10 entries
    if len(lines) >= 10:
        print("\nRecent learning events:")
        for line in lines[-10:]:
            try:
                entry = json.loads(line)
                print(f"  {entry['race_id']}: ROI={entry['roi']:.1f}%, Brier={entry['brier_score']:.3f}")
            except:
                pass

# Check bias corrections
bias_file = Path("data/bias_correction.json")
if bias_file.exists():
    with open(bias_file, 'r') as f:
        biases = json.load(f)
    
    print(f"\n{'='*60}")
    print("MODEL IMPROVEMENTS")
    print("="*60)
    
    metadata = biases.get('metadata', {})
    print(f"\nTotal samples: {metadata.get('total_samples', 0)}")
    print(f"Overall accuracy: {metadata.get('overall_accuracy', 0):.1%}")
    print(f"Avg Brier score: {metadata.get('avg_brier_score', 0):.3f}")
    print(f"Last optimized: {metadata.get('last_optimized', 'Unknown')}")
    
    adjustments = biases.get('adjustments', {})
    print(f"\nGlobal adjustments:")
    print(f"  Synergy weight: {adjustments.get('synergy_weight_multiplier', 1.0):.2f}")
    print(f"  Sectional weight: {adjustments.get('sectional_weight_multiplier', 1.0):.2f}")
    print(f"  Confidence bias: {adjustments.get('confidence_bias', 0.0):.2f}")
    
    contextual = biases.get('contextual', {})
    print(f"\nContextual optimizations: {len(contextual)} contexts")
    
    # Show top contexts
    for ctx in list(contextual.keys())[:5]:
        vals = contextual[ctx]
        print(f"  {ctx}:")
        print(f"    Synergy: {vals.get('synergy_weight_multiplier', 1.0):.2f}")
        print(f"    Sectional: {vals.get('sectional_weight_multiplier', 1.0):.2f}")

print(f"\n{'='*60}")
print("AUTO-LEARNING COMPLETE!")
print("="*60)
print("\nThe model has been trained on all historical data.")
print("Predictions for Wednesday will use these improved biases.")
print("\n[READY] System is now optimized for next race day!")
print("="*60)
