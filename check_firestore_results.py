"""
Check Firestore for historical results
"""
from google.cloud import firestore
from google.oauth2 import service_account
from collections import Counter

print("="*60)
print("FIRESTORE HISTORICAL DATA CHECK")
print("="*60)

PROJECT_ID = "hkjc-v2"
CREDS_PATH = "c:/Users/ASUS/hkjc/service-account-key.json"

try:
    # Load credentials
    creds = service_account.Credentials.from_service_account_file(CREDS_PATH)
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    
    print("\n[INFO] Connected to Firestore")
    
    # Check results collection
    print("\n[INFO] Checking 'results' collection...")
    results_ref = db.collection("results")
    
    # Get all results
    results = list(results_ref.stream())
    
    print(f"\n[OK] Found {len(results)} result documents in Firestore!")
    
    if results:
        # Analyze the data
        dates = []
        venues = []
        
        for doc in results:
            data = doc.to_dict()
            race_id = data.get('race_id', doc.id)
            
            if race_id:
                parts = race_id.split('_')
                if len(parts) >= 2:
                    date = parts[0]
                    venue = parts[1]
                    dates.append(date)
                    venues.append(venue)
        
        if dates:
            print(f"\nDate range: {min(dates)} to {max(dates)}")
            print(f"Unique dates: {len(set(dates))}")
            
            venue_counts = Counter(venues)
            print(f"\nBy venue:")
            for venue, count in venue_counts.most_common():
                print(f"  {venue}: {count} races")
            
            # Show sample
            print(f"\nSample result IDs (first 10):")
            for doc in results[:10]:
                print(f"  {doc.id}")
        
        # Check if they have dividends
        print(f"\n[INFO] Checking dividend data...")
        with_dividends = 0
        without_dividends = 0
        
        for doc in results[:50]:  # Sample first 50
            data = doc.to_dict()
            dividends = data.get('dividends', {})
            win_divs = dividends.get('WIN', [])
            
            if win_divs:
                with_dividends += 1
            else:
                without_dividends += 1
        
        print(f"Sample of 50 results:")
        print(f"  With dividends: {with_dividends}")
        print(f"  Without dividends: {without_dividends}")
    
    # Check predictions collection
    print(f"\n{'='*60}")
    print("[INFO] Checking 'predictions' collection...")
    predictions_ref = db.collection("predictions")
    predictions = list(predictions_ref.stream())
    
    print(f"\n[OK] Found {len(predictions)} prediction documents in Firestore!")
    
    if predictions:
        print(f"\nSample prediction IDs (first 10):")
        for doc in predictions[:10]:
            print(f"  {doc.id}")
    
    # Summary
    print(f"\n{'='*60}")
    print("FIRESTORE SUMMARY")
    print("="*60)
    print(f"Results: {len(results)} races")
    print(f"Predictions: {len(predictions)} races")
    
    if len(results) >= 1000:
        print(f"\n[EXCELLENT] You have {len(results)} results in Firestore!")
        print("This is MORE than enough for training!")
    elif len(results) >= 500:
        print(f"\n[GOOD] You have {len(results)} results in Firestore")
        print("This is decent for training")
    else:
        print(f"\n[OK] You have {len(results)} results in Firestore")
    
    print("\n[ACTION] You can download these to local storage for training!")
    
except Exception as e:
    print(f"\n[ERROR] Failed to check Firestore: {e}")

print("\n" + "="*60)
