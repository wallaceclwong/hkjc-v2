"""
Sync Firestore Historical Data to Local Storage
NO BILLABLE OPERATIONS - Only downloads existing data
"""
from google.cloud import firestore
from google.oauth2 import service_account
import json
from pathlib import Path

print("="*60)
print("FIRESTORE TO LOCAL SYNC")
print("="*60)
print("\n[INFO] This script only DOWNLOADS data - no charges")
print("[INFO] Reading from Firestore, writing to local files")

PROJECT_ID = "hkjc-v2"
CREDS_PATH = "c:/Users/ASUS/hkjc/service-account-key.json"

# Directories
RESULTS_DIR = Path("data/results")
PREDICTIONS_DIR = Path("data/predictions")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

try:
    # Connect to Firestore
    creds = service_account.Credentials.from_service_account_file(CREDS_PATH)
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    
    print("\n[OK] Connected to Firestore")
    
    # Sync Results
    print("\n" + "="*60)
    print("SYNCING RESULTS")
    print("="*60)
    
    results_ref = db.collection("results")
    results = list(results_ref.stream())
    
    print(f"\nFound {len(results)} results in Firestore")
    print("Downloading to local storage...")
    
    synced_results = 0
    skipped_results = 0
    
    for i, doc in enumerate(results):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(results)}")
        
        race_id = doc.id
        local_file = RESULTS_DIR / f"results_{race_id}.json"
        
        # Skip if already exists
        if local_file.exists():
            skipped_results += 1
            continue
        
        # Download and save
        data = doc.to_dict()
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        synced_results += 1
    
    print(f"\n[OK] Results synced: {synced_results}")
    print(f"[INFO] Already existed: {skipped_results}")
    print(f"[INFO] Total local results: {synced_results + skipped_results}")
    
    # Sync Predictions
    print("\n" + "="*60)
    print("SYNCING PREDICTIONS")
    print("="*60)
    
    predictions_ref = db.collection("predictions")
    predictions = list(predictions_ref.stream())
    
    print(f"\nFound {len(predictions)} predictions in Firestore")
    print("Downloading to local storage...")
    
    synced_preds = 0
    skipped_preds = 0
    
    for i, doc in enumerate(predictions):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(predictions)}")
        
        race_id = doc.id
        local_file = PREDICTIONS_DIR / f"prediction_{race_id}.json"
        
        # Skip if already exists
        if local_file.exists():
            skipped_preds += 1
            continue
        
        # Download and save
        data = doc.to_dict()
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        synced_preds += 1
    
    print(f"\n[OK] Predictions synced: {synced_preds}")
    print(f"[INFO] Already existed: {skipped_preds}")
    print(f"[INFO] Total local predictions: {synced_preds + skipped_preds}")
    
    # Summary
    print("\n" + "="*60)
    print("SYNC COMPLETE")
    print("="*60)
    
    total_results = synced_results + skipped_results
    total_preds = synced_preds + skipped_preds
    
    print(f"\nLocal storage now has:")
    print(f"  Results: {total_results} races")
    print(f"  Predictions: {total_preds} races")
    
    # Calculate matched pairs
    result_ids = {f.stem.replace('results_', '') for f in RESULTS_DIR.glob('results_*.json')}
    pred_ids = {f.stem.replace('prediction_', '') for f in PREDICTIONS_DIR.glob('prediction_*.json')}
    matched = result_ids & pred_ids
    
    print(f"\nMatched pairs (for training): {len(matched)}")
    
    if len(matched) >= 1000:
        print("\n[EXCELLENT] You now have 1000+ training pairs!")
        print("Auto-learning can use all this data to improve the model")
    elif len(matched) >= 500:
        print("\n[GOOD] You have 500+ training pairs")
        print("This is enough for decent model training")
    else:
        print(f"\n[INFO] You have {len(matched)} training pairs")
    
    print("\n[NEXT STEP] Run auto-learning on all historical data")
    print("Command: python services/auto_learning.py --all")
    
except Exception as e:
    print(f"\n[ERROR] Sync failed: {e}")

print("\n" + "="*60)
