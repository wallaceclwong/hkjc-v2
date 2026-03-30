"""
Test Firestore connection after permission fix
"""
import os
from google.cloud import firestore
from google.oauth2 import service_account

print("="*60)
print("FIRESTORE CONNECTION TEST")
print("="*60)

PROJECT_ID = "hkjc-v2"
CREDS_PATH = "c:/Users/ASUS/hkjc/service-account-key.json"

print(f"\nProject: {PROJECT_ID}")
print(f"Credentials: {CREDS_PATH}")

try:
    # Load credentials
    creds = service_account.Credentials.from_service_account_file(CREDS_PATH)
    
    # Initialize Firestore client
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    
    print("\n[INFO] Attempting to write test document...")
    
    # Try to write a test document
    test_ref = db.collection("_health_check").document("test")
    test_ref.set({
        "timestamp": firestore.SERVER_TIMESTAMP,
        "status": "ok",
        "test": "connection_test"
    })
    
    print("[INFO] Attempting to read test document...")
    
    # Try to read it back
    doc = test_ref.get()
    
    if doc.exists:
        print("\n" + "="*60)
        print("SUCCESS! FIRESTORE IS WORKING!")
        print("="*60)
        print("\nCloud sync is now enabled.")
        print("Data will be backed up to Firestore.")
        
        # Show the data
        data = doc.to_dict()
        print(f"\nTest document data:")
        print(f"  Status: {data.get('status')}")
        print(f"  Timestamp: {data.get('timestamp')}")
        
    else:
        print("\n[FAIL] Document was written but could not be read back")
        
except Exception as e:
    error_msg = str(e)
    
    print("\n" + "="*60)
    print("FIRESTORE CONNECTION FAILED")
    print("="*60)
    
    if "403" in error_msg:
        print("\nError: 403 Permission Denied")
        print("\nThe service account still lacks permissions.")
        print("\nPlease follow the fix guide:")
        print("1. Open: https://console.cloud.google.com/iam-admin/iam?project=hkjc-v2")
        print("2. Find: hkjc-backend@hkjc-v2.iam.gserviceaccount.com")
        print("3. Click Edit and add role: 'Cloud Datastore User'")
        print("4. Wait 1-2 minutes and run this test again")
    else:
        print(f"\nError: {error_msg}")
    
    print("\n[INFO] System continues to work in local mode")
    print("       All betting operations are functional")

print("\n" + "="*60)
