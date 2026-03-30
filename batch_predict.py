"""
Batch Prediction Script
Generate predictions for all races in a meeting at once
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_prediction(date, venue, race_no):
    """Run prediction for a single race"""
    py = str(Path('.venv') / 'Scripts' / 'python.exe')
    script = str(Path('services') / 'prediction_engine.py')
    
    cmd = [py, script, '--date', date, '--venue', venue, '--race', str(race_no)]
    
    print(f"\n{'='*60}")
    print(f"Race {race_no} - {venue} {date}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[OK] Prediction generated for Race {race_no}")
        return True
    else:
        print(f"[ERROR] Failed: {result.stderr[:200]}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_predict.py <date> <venue> [max_races]")
        print("Example: python batch_predict.py 2026-04-01 ST 11")
        sys.exit(1)
    
    date = sys.argv[1]
    venue = sys.argv[2]
    max_races = int(sys.argv[3]) if len(sys.argv) > 3 else 11
    
    print("="*60)
    print("BATCH PREDICTION")
    print("="*60)
    print(f"\nDate: {date}")
    print(f"Venue: {venue}")
    print(f"Races: 1-{max_races}")
    print(f"\n[WARNING] This will use Vertex AI - costs ~$0.20 per race")
    print(f"[WARNING] Total cost: ~${0.20 * max_races:.2f}")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled")
        sys.exit(0)
    
    print("\nStarting batch prediction...")
    start_time = datetime.now()
    
    success_count = 0
    failed_races = []
    
    for race_no in range(1, max_races + 1):
        if run_prediction(date, venue, race_no):
            success_count += 1
        else:
            failed_races.append(race_no)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("BATCH PREDICTION COMPLETE")
    print("="*60)
    print(f"\nSuccessful: {success_count}/{max_races}")
    print(f"Failed: {len(failed_races)}")
    if failed_races:
        print(f"Failed races: {failed_races}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Estimated cost: ${0.20 * success_count:.2f}")
    
    print("\nNext steps:")
    print("1. Review predictions in data/predictions/")
    print("2. Filter for confidence > 70%")
    print("3. Place bets on high-confidence picks")

if __name__ == '__main__':
    main()
