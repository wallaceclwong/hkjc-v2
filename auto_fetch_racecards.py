"""
Automated Racecard Fetching
Checks if racecards are available and fetches them automatically
100% FREE - No API calls
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import glob

def get_upcoming_race_dates(days_ahead=7):
    """Get potential race dates for next N days"""
    dates = []
    today = datetime.now()
    
    for i in range(days_ahead):
        date = today + timedelta(days=i)
        # HKJC typically races on Wed, Sat, Sun
        if date.weekday() in [2, 5, 6]:  # Wed=2, Sat=5, Sun=6
            dates.append(date.strftime('%Y-%m-%d'))
    
    return dates

def check_racecard_exists(date, venue):
    """Check if racecard already exists"""
    date_compact = date.replace('-', '')
    pattern = f"data/racecard_{date_compact}_R*.json"
    files = glob.glob(pattern)
    return len(files) > 0

def fetch_racecard(date, venue):
    """Try to fetch racecard for a specific date/venue"""
    py = str(Path('.venv') / 'Scripts' / 'python.exe')
    script = str(Path('scripts') / 'smart_racecard_fetcher.py')
    
    # Convert date format
    date_slash = date.replace('-', '/')
    
    cmd = [py, script, '--date', date_slash, '--venue', venue]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        # Check if files were created
        if check_racecard_exists(date, venue):
            return True, "Racecards fetched successfully"
        else:
            return False, "No racecards created (not available yet)"
    else:
        error = result.stderr[:200] if result.stderr else "Unknown error"
        return False, error

def main():
    print("="*60)
    print("AUTOMATED RACECARD FETCHING")
    print("="*60)
    print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get command line args or use auto mode
    if len(sys.argv) >= 3:
        dates = [sys.argv[1]]
        venues = [sys.argv[2]]
        print(f"\nManual mode: {dates[0]} {venues[0]}")
    else:
        dates = get_upcoming_race_dates(7)
        venues = ['ST', 'HV']
        print(f"\nAuto mode: Checking next 7 days")
        print(f"Potential race dates: {dates}")
    
    print("\n" + "="*60)
    print("CHECKING RACECARDS")
    print("="*60)
    
    fetched_count = 0
    already_exists = 0
    not_available = 0
    
    for date in dates:
        for venue in venues:
            print(f"\n{date} {venue}:")
            
            # Check if already exists
            if check_racecard_exists(date, venue):
                print(f"  [EXISTS] Racecards already downloaded")
                already_exists += 1
                continue
            
            # Try to fetch
            print(f"  [CHECKING] Attempting to fetch...")
            success, message = fetch_racecard(date, venue)
            
            if success:
                print(f"  [OK] {message}")
                fetched_count += 1
            else:
                print(f"  [SKIP] {message}")
                not_available += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nNewly fetched: {fetched_count}")
    print(f"Already exists: {already_exists}")
    print(f"Not available yet: {not_available}")
    
    if fetched_count > 0:
        print("\n[SUCCESS] New racecards fetched!")
        print("\nNext steps:")
        print("1. Generate predictions: python batch_predict.py <date> <venue> 11")
        print("2. Filter high confidence: python filter_high_confidence.py <date> <venue>")
    elif already_exists > 0:
        print("\n[INFO] Racecards already available")
        print("Ready to generate predictions")
    else:
        print("\n[INFO] No new racecards available yet")
        print("Try again later (usually available Tuesday night)")
    
    print("="*60)

if __name__ == '__main__':
    main()
