import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import Config
from google.cloud import firestore

def inspect_racecards():
    print(f"Project: {Config.PROJECT_ID}")
    db = firestore.Client(project=Config.PROJECT_ID, database=Config.FIRESTORE_DATABASE)
    
    print("\n--- Latest 3 Racecards ---")
    docs = db.collection(Config.COL_RACECARDS).limit(3).get()
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id}")
        horses = data.get("horses", [])
        if horses:
            print(f"  Example Horse: {horses[0].get('horse_name')} (Saddle: {horses[0].get('saddle_number')})")
        else:
            print("  No horses found in this document.")

if __name__ == "__main__":
    inspect_racecards()
