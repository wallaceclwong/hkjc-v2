import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config

def test_firestore_init():
    print(f"Testing Firestore Initialization for Project: {Config.PROJECT_ID}")
    try:
        db = Config.get_firestore_client()
        print("[OK] Firestore client successfully initialized.")
        print(f"  Target Project: {db.project}")
        print(f"  Target Database: {db.database}")
        
        # Note: We don't attempt a write because the project/DB likely doesn't exist yet
        print("\n[INFO] To perform actual database operations, please ensure:")
        print(f"1. GCP Project '{Config.PROJECT_ID}' exists.")
        print("2. Firestore is enabled in Native Mode.")
        print("3. GOOGLE_APPLICATION_CREDENTIALS points to a valid service account JSON.")
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize Firestore client: {e}")

if __name__ == "__main__":
    test_firestore_init()
