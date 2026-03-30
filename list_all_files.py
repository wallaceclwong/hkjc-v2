import os
import glob

# List all prediction files
pred_files = glob.glob("c:/Users/ASUS/hkjc/data/predictions/*.json")
print(f"Found {len(pred_files)} prediction files:")
for f in sorted(pred_files)[-5:]:  # Show last 5
    print(f"  {os.path.basename(f)}")

# List all result files  
result_files = glob.glob("c:/Users/ASUS/hkjc/data/results/*.json")
print(f"\nFound {len(result_files)} result files:")
for f in sorted(result_files)[-5:]:  # Show last 5
    print(f"  {os.path.basename(f)}")

# Check for March 29 specifically
march29_pred = [f for f in pred_files if "20260329" in f]
march29_res = [f for f in result_files if "20260329" in f]

print(f"\nMarch 29 files:")
print(f"  Predictions: {len(march29_pred)}")
print(f"  Results: {len(march29_res)}")
