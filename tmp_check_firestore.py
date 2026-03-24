import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import Config
from google.cloud import firestore

def inspect():
    print(f"Project: {Config.PROJECT_ID}")
    db = firestore.Client(project=Config.PROJECT_ID, database=Config.FIRESTORE_DATABASE)
    
    print("\n--- Latest 5 Predictions ---")
    docs = db.collection("predictions").order_by("race_id", direction=firestore.Query.DESCENDING).limit(5).get()
    for doc in docs:
        print(f"ID: {doc.id} -> {doc.to_dict().keys()}")
        if doc.id.startswith("N/A"):
            print("ALERT: Found N/A document ID!")

if __name__ == "__main__":
    inspect()
