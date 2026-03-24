import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import Config
from google.cloud import firestore

def list_racecards():
    db = firestore.Client(project=Config.PROJECT_ID, database=Config.FIRESTORE_DATABASE)
    print(f"Checking collection: {Config.COL_RACECARDS}")
    docs = db.collection(Config.COL_RACECARDS).limit(10).get()
    for doc in docs:
        print(f"Found ID: {doc.id}")

if __name__ == "__main__":
    list_racecards()
