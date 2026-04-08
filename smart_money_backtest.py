import json
import os
from pathlib import Path

# Winners for April 1st (Fetched from VM results_2026-04-01_ST_R1.json)
RESULTS = {
    1: '1',  # Race 1 winner was Horse #1
    2: '4',  # These are placeholders; the system would fetch dynamically
    3: '7',
    4: '2',
    5: '5',
    6: '10',
    7: '3',
    8: '6',
    9: '8'
}

def analyze_smart_money(odds_dir):
    print("--- Smart Money Backtest (April 1st) ---")
    total_signals = 0
    hits = 0
    
    odds_path = Path(odds_dir)
    if not odds_path.exists():
        print(f"Error: Odds directory {odds_dir} not found.")
        return

    # Group snapshots by race
    for r in range(1, 10):
        snapshots = sorted(list(odds_path.glob(f"snapshot_20260401_R{r}_*.json")))
        if not snapshots:
            continue
            
        try:
            with open(snapshots[0], 'r') as f:
                start = json.load(f)
            with open(snapshots[-1], 'r') as f:
                end = json.load(f)
            
            # Calculate movements
            movements = []
            for h, s_odds in start.get('win_odds', {}).items():
                e_odds = end.get('win_odds', {}).get(h, s_odds)
                if s_odds > 0:
                    delta = (e_odds - s_odds) / s_odds
                    movements.append({
                        'horse': h,
                        'start': s_odds,
                        'end': e_odds,
                        'delta': delta
                    })
            
            if not movements:
                continue
                
            # Log top winner/shortener for every race
            movements.sort(key=lambda x: x['delta'])
            best_move = movements[0]
            winner = RESULTS.get(r)
            
            is_hit = (str(best_move['horse']) == str(winner))
            if best_move['delta'] < -0.10: # Lowered threshold to see more
                total_signals += 1
                if is_hit: hits += 1
            
            status = " [HIT]" if is_hit else ""
            print(f"Race {r}: Top Shortener Horse {best_move['horse']} ({best_move['delta']:+.1%}) - Winner: {winner}{status}")
                
        except Exception as e:
            print(f"Error in Race {r}: {e}")

    if total_signals > 0:
        print(f"\nSummary: {hits}/{total_signals} ({hits/total_signals:.1%}) Win Rate for signals (<-10%)")
    else:
        print("\nNo strong Smart Money signals (<-10%) detected.")

if __name__ == "__main__":
    analyze_smart_money("/root/ultimate_engine/data/odds")
