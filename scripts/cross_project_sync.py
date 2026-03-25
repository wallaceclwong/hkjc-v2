import os
import sys
import json
from google.cloud import firestore
from google.oauth2 import service_account
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config

def sync_collections(source_project, dest_key_path, collections):
    """
    Syncs documents from source_project (default creds) to destination (service account key).
    """
    # 1. Initialize Source (Default Auth)
    logger.info(f"💾 Initializing Source Firestore: {source_project}")
    source_db = firestore.Client(project=source_project)

    # 2. Initialize Destination (Key Auth)
    logger.info(f"🎯 Initializing Destination Firestore: hkjc-v2")
    creds = service_account.Credentials.from_service_account_file(dest_key_path)
    dest_db = firestore.Client(project="hkjc-v2", credentials=creds)

    for col_name in collections:
        logger.info(f"🔄 Syncing collection: {col_name}...")
        source_ref = source_db.collection(col_name)
        docs = source_ref.stream()

        count = 0
        batch = dest_db.batch()
        
        for doc in docs:
            data = doc.to_dict()
            dest_ref = dest_db.collection(col_name).document(doc.id)
            batch.set(dest_ref, data)
            count += 1
            
            if count % 500 == 0:
                batch.commit()
                batch = dest_db.batch()
                logger.info(f"  - Synced {count} documents...")

        batch.commit()
        logger.success(f"✅ Finished syncing {count} documents for {col_name}.")

if __name__ == "__main__":
    SOURCE_PROJECT = "project-6172aadc-bdc0-43ee-8ac"
    DEST_KEY = "c:\\Users\\ASUS\\hkjc\\service-account-key.json"
    COLLECTIONS = [Config.COL_PREDICTIONS, Config.COL_RESULTS, Config.COL_ANALYTICAL, Config.COL_RACECARDS]

    sync_collections(SOURCE_PROJECT, DEST_KEY, COLLECTIONS)
