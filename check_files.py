import os
import glob

# Check for prediction files
pred_files = glob.glob("c:/Users/ASUS/hkjc/data/predictions/prediction_20260329*.json")
print("Prediction files for March 29:")
for f in pred_files:
    print(f"  {os.path.basename(f)}")

# Check for result files
result_files = glob.glob("c:/Users/ASUS/hkjc/data/results/results_20260329*.json")
print("\nResult files for March 29:")
for f in result_files:
    print(f"  {os.path.basename(f)}")

# Check if we have at least one race
if pred_files and result_files:
    # Extract race number from first file
    pred_file = pred_files[0]
    race_id = os.path.basename(pred_file).replace("prediction_", "").replace(".json", "")
    print(f"\nTesting auto-learning with race: {race_id}")
    
    # Run auto-learning
    import sys
    sys.path.append("c:/Users/ASUS/hkjc")
    from services.auto_learning import trigger_auto_learning_for_race
    trigger_auto_learning_for_race(race_id)
else:
    print("\nNo matching files found for auto-learning")
