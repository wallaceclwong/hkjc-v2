"""
Automated Post-Race Workflow
Fetches results and runs auto-learning automatically
100% FREE - No API calls
"""
import subprocess
import sys
import glob
from pathlib import Path
from datetime import datetime, timedelta

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[OK] {description} complete")
        if result.stdout:
            print(result.stdout[-500:])  # Last 500 chars
        return True
    else:
        print(f"[ERROR] {description} failed")
        print(result.stderr[:500])
        return False

def get_recent_race_dates(days_back=7):
    """Get race dates from last N days that might have results"""
    dates = []
    today = datetime.now()
    
    for i in range(days_back):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        dates.append(date_str)
    
    return dates

def main():
    if len(sys.argv) < 3:
        print("Usage: python auto_fetch_and_learn.py <date> <venue>")
        print("Example: python auto_fetch_and_learn.py 2026-04-01 ST")
        print("\nOr use 'auto' to fetch recent races:")
        print("python auto_fetch_and_learn.py auto auto")
        sys.exit(1)
    
    date = sys.argv[1]
    venue = sys.argv[2]
    
    print("="*60)
    print("AUTOMATED POST-RACE WORKFLOW")
    print("="*60)
    print(f"\nDate: {date}")
    print(f"Venue: {venue}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    py = str(Path('.venv') / 'Scripts' / 'python.exe')
    
    # Step 1: Fetch results
    if date == 'auto':
        print("\n[INFO] Auto mode - checking recent dates")
        dates = get_recent_race_dates(7)
        venues = ['ST', 'HV']
        
        fetched_any = False
        for d in dates:
            for v in venues:
                cmd = [py, 'services/results_ingest.py', '--date', d, '--venue', v]
                if run_command(cmd, f"Fetching results for {d} {v}"):
                    fetched_any = True
        
        if not fetched_any:
            print("\n[WARN] No new results fetched")
    else:
        cmd = [py, 'services/results_ingest.py', '--date', date, '--venue', venue]
        if not run_command(cmd, f"Fetching results for {date} {venue}"):
            print("\n[ERROR] Failed to fetch results, stopping")
            sys.exit(1)
    
    # Step 2: Run auto-learning on ALL historical data
    print("\n[INFO] Running auto-learning on all matched pairs...")
    cmd = [py, 'run_full_auto_learning.py']
    run_command(cmd, "Auto-learning")
    
    # Step 3: Show summary
    print("\n" + "="*60)
    print("WORKFLOW COMPLETE")
    print("="*60)
    
    # Check bias corrections
    bias_file = Path('data/bias_correction.json')
    if bias_file.exists():
        import json
        with open(bias_file, 'r') as f:
            biases = json.load(f)
        
        metadata = biases.get('metadata', {})
        print(f"\nModel Status:")
        print(f"  Total samples: {metadata.get('total_samples', 0)}")
        print(f"  Overall accuracy: {metadata.get('overall_accuracy', 0):.1%}")
        print(f"  Avg Brier score: {metadata.get('avg_brier_score', 0):.3f}")
        print(f"  Last optimized: {metadata.get('last_optimized', 'Unknown')}")
        
        adjustments = biases.get('adjustments', {})
        print(f"\nCurrent Adjustments:")
        print(f"  Synergy weight: {adjustments.get('synergy_weight_multiplier', 1.0):.2f}")
        print(f"  Sectional weight: {adjustments.get('sectional_weight_multiplier', 1.0):.2f}")
        print(f"  Confidence bias: {adjustments.get('confidence_bias', 0.0):.2f}")
    
    print("\n[READY] System updated and ready for next race day!")
    print("="*60)

if __name__ == '__main__':
    main()
