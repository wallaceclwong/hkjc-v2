"""
Debug why backtest only processed 1 race
"""
import glob
import json
from pathlib import Path

print("Checking data quality...")

# Sample a few predictions and results
pred_files = glob.glob('data/predictions/prediction_*.json')[:10]
result_files = glob.glob('data/results/results_*.json')[:10]

print(f"\nChecking {len(pred_files)} sample predictions:")
for f in pred_files:
    race_id = Path(f).stem.replace('prediction_', '')
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            pred = json.load(file)
        
        has_rec = 'recommended_bet' in pred
        has_kelly = 'kelly_stakes' in pred and pred['kelly_stakes']
        has_probs = 'probabilities' in pred and pred['probabilities']
        
        print(f"  {race_id}: Rec={has_rec}, Kelly={has_kelly}, Probs={has_probs}")
    except Exception as e:
        print(f"  {race_id}: ERROR - {e}")

print(f"\nChecking {len(result_files)} sample results:")
for f in result_files:
    race_id = Path(f).stem.replace('results_', '')
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            result = json.load(file)
        
        has_results = 'results' in result and result['results']
        has_dividends = 'dividends' in result and result.get('dividends', {}).get('WIN')
        
        winner = None
        winner_div = 0
        
        if has_results:
            for h in result['results']:
                if h.get('plc') == '1':
                    winner = h.get('horse_no')
                    break
        
        if has_dividends:
            for div in result['dividends']['WIN']:
                if div.get('combination') == str(winner):
                    winner_div = div.get('dividend', 0)
                    break
        
        print(f"  {race_id}: Winner={winner}, Dividend={winner_div}, HasDiv={has_dividends}")
    except Exception as e:
        print(f"  {race_id}: ERROR - {e}")

# Check one matched pair in detail
print("\n" + "="*60)
print("Detailed check of one matched pair:")
print("="*60)

pred_file = 'data/predictions/prediction_2026-03-29_ST_R1.json'
result_file = 'data/results/results_2026-03-29_ST_R1.json'

if Path(pred_file).exists() and Path(result_file).exists():
    with open(pred_file, 'r', encoding='utf-8') as f:
        pred = json.load(f)
    with open(result_file, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print("\nPrediction:")
    print(f"  Recommended: {pred.get('recommended_bet')}")
    print(f"  Kelly stakes: {pred.get('kelly_stakes')}")
    print(f"  Probabilities: {list(pred.get('probabilities', {}).keys())[:5]}")
    
    print("\nResult:")
    print(f"  Winner: {[h for h in result.get('results', []) if h.get('plc') == '1']}")
    print(f"  Dividends: {result.get('dividends', {}).get('WIN', [])[:2]}")
