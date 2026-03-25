import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.firestore_service import FirestoreService
from config.settings import Config

def check_and_cleanup():
    fs = FirestoreService()
    print(f"Checking {Config.PROJECT_ID} for future docs...")
    
    # Query for anything after today
    docs = fs.query(Config.COL_PREDICTIONS, filters=[("race_id", ">=", "2026-03-26")])
    
    if not docs:
        print("No future docs found.")
        return

    print(f"Found {len(docs)} future docs.")
    for d in docs:
        race_id = d.get("race_id")
        print(f"Deleting stray doc: {race_id}")
        fs.delete(Config.COL_PREDICTIONS, race_id)
        
    print("Cleanup complete.")

if __name__ == "__main__":
    check_and_cleanup()
