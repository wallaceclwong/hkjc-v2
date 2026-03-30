"""
Backtesting Framework for HKJC Betting System
Tests historical predictions against actual results
100% FREE - No API calls, just analysis
"""
import glob
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

print("="*60)
print("BETTING SYSTEM BACKTESTING")
print("="*60)
print("\n[INFO] Testing predictions on historical data")
print("[INFO] Calculating ROI for different strategies")

# Load matched prediction-result pairs
pred_files = {Path(f).stem.replace('prediction_', ''): f for f in glob.glob('data/predictions/prediction_*.json')}
result_files = {Path(f).stem.replace('results_', ''): f for f in glob.glob('data/results/results_*.json')}

matched_ids = set(pred_files.keys()) & set(result_files.keys())
print(f"\nFound {len(matched_ids)} matched prediction-result pairs")

# Initialize tracking
strategies = {
    'ai_top_pick': {'name': 'AI Top Pick ($100 flat)', 'bets': 0, 'wins': 0, 'stake': 0, 'return': 0, 'races': []},
    'kelly_stakes': {'name': 'Kelly Stakes (optimized)', 'bets': 0, 'wins': 0, 'stake': 0, 'return': 0, 'races': []},
    'top_2_horses': {'name': 'Top 2 Horses ($50 each)', 'bets': 0, 'wins': 0, 'stake': 0, 'return': 0, 'races': []},
    'high_confidence': {'name': 'High Confidence Only (>70%)', 'bets': 0, 'wins': 0, 'stake': 0, 'return': 0, 'races': []}
}

# Track by venue and month
venue_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'stake': 0, 'return': 0})
monthly_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'stake': 0, 'return': 0})

print("\n" + "="*60)
print("RUNNING BACKTEST")
print("="*60)

processed = 0
for i, race_id in enumerate(sorted(matched_ids)):
    if i % 100 == 0:
        print(f"  Progress: {i}/{len(matched_ids)}")
    
    try:
        # Load prediction and result
        with open(pred_files[race_id], 'r', encoding='utf-8', errors='ignore') as f:
            pred = json.load(f)
        with open(result_files[race_id], 'r', encoding='utf-8', errors='ignore') as f:
            result = json.load(f)
        
        # Get race info
        parts = race_id.split('_')
        if len(parts) < 2:
            continue
        
        date = parts[0]
        venue = parts[1]
        month = date[:7] if len(date) >= 7 else 'Unknown'
        
        # Find winner from dividends (more reliable)
        winner = None
        winner_dividend = 0
        
        dividends = result.get('dividends', {}).get('WIN', [])
        if dividends and len(dividends) > 0:
            # Winner is the horse with dividend listed
            winner = str(dividends[0].get('combination', ''))
            try:
                winner_dividend = float(dividends[0].get('dividend', 0))
            except:
                winner_dividend = 0
        
        # Fallback: check results list
        if not winner:
            results_list = result.get('results', [])
            if results_list:
                # First horse in results is usually the winner
                winner = str(results_list[0].get('horse_no', ''))
        
        if not winner or winner_dividend == 0:
            continue
        
        processed += 1
        
        # Strategy 1: AI Top Pick
        recommended = pred.get('recommended_bet', '')
        if 'WIN' in recommended:
            top_pick = recommended.split()[-1]
            stake = 100
            strategies['ai_top_pick']['bets'] += 1
            strategies['ai_top_pick']['stake'] += stake
            
            if top_pick == winner:
                payout = (winner_dividend / 10.0) * stake
                strategies['ai_top_pick']['return'] += payout
                strategies['ai_top_pick']['wins'] += 1
                strategies['ai_top_pick']['races'].append({
                    'race_id': race_id,
                    'pick': top_pick,
                    'stake': stake,
                    'return': payout,
                    'profit': payout - stake
                })
        
        # Strategy 2: Kelly Stakes
        kelly_stakes = pred.get('kelly_stakes', {})
        if kelly_stakes:
            race_stake = sum(kelly_stakes.values())
            race_return = 0
            
            for horse, stake in kelly_stakes.items():
                strategies['kelly_stakes']['stake'] += stake
                strategies['kelly_stakes']['bets'] += 1
                
                if horse == winner:
                    payout = (winner_dividend / 10.0) * stake
                    race_return += payout
                    strategies['kelly_stakes']['wins'] += 1
            
            strategies['kelly_stakes']['return'] += race_return
            
            if race_return > 0:
                strategies['kelly_stakes']['races'].append({
                    'race_id': race_id,
                    'stakes': kelly_stakes,
                    'total_stake': race_stake,
                    'return': race_return,
                    'profit': race_return - race_stake
                })
        
        # Strategy 3: Top 2 Horses
        probs = pred.get('probabilities', {})
        if probs:
            top_2 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:2]
            stake_per_horse = 50
            
            for horse, prob in top_2:
                strategies['top_2_horses']['bets'] += 1
                strategies['top_2_horses']['stake'] += stake_per_horse
                
                if horse == winner:
                    payout = (winner_dividend / 10.0) * stake_per_horse
                    strategies['top_2_horses']['return'] += payout
                    strategies['top_2_horses']['wins'] += 1
                    strategies['top_2_horses']['races'].append({
                        'race_id': race_id,
                        'pick': horse,
                        'stake': stake_per_horse,
                        'return': payout,
                        'profit': payout - stake_per_horse
                    })
        
        # Strategy 4: High Confidence Only
        confidence = pred.get('confidence_score', 0)
        if confidence > 0.70 and probs:
            top_horse = max(probs.items(), key=lambda x: x[1])
            horse, prob = top_horse
            stake = 100
            
            strategies['high_confidence']['bets'] += 1
            strategies['high_confidence']['stake'] += stake
            
            if horse == winner:
                payout = (winner_dividend / 10.0) * stake
                strategies['high_confidence']['return'] += payout
                strategies['high_confidence']['wins'] += 1
                strategies['high_confidence']['races'].append({
                    'race_id': race_id,
                    'pick': horse,
                    'confidence': confidence,
                    'stake': stake,
                    'return': payout,
                    'profit': payout - stake
                })
        
        # Track by venue
        venue_stats[venue]['races'] += 1
        monthly_stats[month]['races'] += 1
        
    except Exception as e:
        continue

print(f"\n[OK] Processed {processed} races with complete data")

# Calculate results
print("\n" + "="*60)
print("BACKTESTING RESULTS")
print("="*60)

for strategy_key, data in strategies.items():
    if data['bets'] == 0:
        continue
    
    roi = ((data['return'] - data['stake']) / data['stake'] * 100) if data['stake'] > 0 else 0
    win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
    profit = data['return'] - data['stake']
    
    print(f"\n{data['name']}")
    print("-"*40)
    print(f"  Total bets: {data['bets']}")
    print(f"  Wins: {data['wins']}")
    print(f"  Win rate: {win_rate:.1f}%")
    print(f"  Total stake: ${data['stake']:.2f}")
    print(f"  Total return: ${data['return']:.2f}")
    print(f"  Profit/Loss: ${profit:.2f}")
    print(f"  ROI: {roi:.1f}%")
    
    # Show best wins
    if data['races']:
        best_wins = sorted(data['races'], key=lambda x: x.get('profit', 0), reverse=True)[:3]
        print(f"\n  Top 3 wins:")
        for win in best_wins:
            print(f"    {win['race_id']}: +${win.get('profit', 0):.2f}")

# Summary comparison
print("\n" + "="*60)
print("STRATEGY COMPARISON")
print("="*60)

print(f"\n{'Strategy':<30} {'ROI':<10} {'Win Rate':<12} {'Profit':<15}")
print("-"*67)

for strategy_key, data in strategies.items():
    if data['bets'] == 0:
        continue
    
    roi = ((data['return'] - data['stake']) / data['stake'] * 100) if data['stake'] > 0 else 0
    win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
    profit = data['return'] - data['stake']
    
    print(f"{data['name']:<30} {roi:>8.1f}% {win_rate:>10.1f}% ${profit:>13.2f}")

# Save results
output = {
    'backtest_date': datetime.now().isoformat(),
    'races_tested': processed,
    'strategies': {}
}

for strategy_key, data in strategies.items():
    if data['bets'] > 0:
        roi = ((data['return'] - data['stake']) / data['stake'] * 100) if data['stake'] > 0 else 0
        win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
        
        output['strategies'][strategy_key] = {
            'name': data['name'],
            'bets': data['bets'],
            'wins': data['wins'],
            'win_rate': win_rate,
            'total_stake': data['stake'],
            'total_return': data['return'],
            'profit': data['return'] - data['stake'],
            'roi': roi
        }

output_file = Path('data/backtest_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"\n[OK] Results saved to: {output_file}")

print("\n" + "="*60)
print("BACKTEST COMPLETE")
print("="*60)
print("\nKey Insights:")
print(f"  - Tested {processed} races with complete data")
print(f"  - Best strategy: Check ROI comparison above")
print(f"  - This shows what WOULD have happened historically")
print("\n[IMPORTANT] Past performance doesn't guarantee future results!")
print("="*60)
