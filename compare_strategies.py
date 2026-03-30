"""
Compare AI Top Picks vs Kelly Stakes Strategy
"""
import json
import glob
from pathlib import Path

print("="*60)
print("AI TOP PICKS vs KELLY STAKES COMPARISON")
print("="*60)

# Load all March 29 predictions and results
pred_files = sorted(glob.glob("data/predictions/prediction_2026-03-29_ST_R*.json"))
result_files = sorted(glob.glob("data/results/results_2026-03-29_ST_R*.json"))

# Match predictions with results
races = []
for pred_file in pred_files:
    race_id = Path(pred_file).stem.replace("prediction_", "")
    result_file = f"data/results/results_{race_id}.json"
    
    if Path(result_file).exists():
        with open(pred_file, 'r') as f:
            pred = json.load(f)
        with open(result_file, 'r') as f:
            result = json.load(f)
        
        races.append({
            "race_id": race_id,
            "prediction": pred,
            "result": result
        })

print(f"\nAnalyzing {len(races)} races from March 29\n")

# Strategy 1: AI Top Pick (recommended_bet)
print("="*60)
print("STRATEGY 1: AI TOP PICK")
print("="*60)

top_pick_stake = 100  # Fixed $100 per race
top_pick_total_stake = 0
top_pick_total_return = 0
top_pick_wins = 0

for race in races:
    pred = race["prediction"]
    result = race["result"]
    
    # Get AI's top pick
    recommended = pred.get("recommended_bet", "")
    if "WIN" in recommended:
        top_pick = recommended.split()[-1]
    else:
        continue
    
    # Get winner
    winner = None
    for h in result.get("results", []):
        if h.get("plc") == "1":
            winner = str(h.get("horse_no"))
            break
    
    # Calculate return
    top_pick_total_stake += top_pick_stake
    
    if top_pick == winner:
        # Find dividend
        for div in result.get("dividends", {}).get("WIN", []):
            if div.get("combination") == winner:
                dividend = float(div.get("dividend", 0))
                payout = (dividend / 10.0) * top_pick_stake
                top_pick_total_return += payout
                top_pick_wins += 1
                print(f"Race {race['race_id']}: WIN! Pick #{top_pick}, Dividend ${dividend}, Return ${payout:.2f}")
                break
    else:
        print(f"Race {race['race_id']}: LOSS. Pick #{top_pick}, Winner #{winner}")

top_pick_roi = ((top_pick_total_return - top_pick_total_stake) / top_pick_total_stake * 100) if top_pick_total_stake > 0 else 0

print(f"\nTop Pick Summary:")
print(f"  Races: {len(races)}")
print(f"  Wins: {top_pick_wins}")
print(f"  Win Rate: {top_pick_wins/len(races)*100:.1f}%")
print(f"  Total Stake: ${top_pick_total_stake:.2f}")
print(f"  Total Return: ${top_pick_total_return:.2f}")
print(f"  ROI: {top_pick_roi:.1f}%")

# Strategy 2: Kelly Stakes
print("\n" + "="*60)
print("STRATEGY 2: KELLY STAKES")
print("="*60)

kelly_total_stake = 0
kelly_total_return = 0
kelly_wins = 0
kelly_bets = 0

for race in races:
    pred = race["prediction"]
    result = race["result"]
    
    kelly_stakes = pred.get("kelly_stakes", {})
    
    if not kelly_stakes:
        print(f"Race {race['race_id']}: No Kelly stakes")
        continue
    
    # Get winner
    winner = None
    for h in result.get("results", []):
        if h.get("plc") == "1":
            winner = str(h.get("horse_no"))
            break
    
    # Calculate returns for each Kelly bet
    race_stake = sum(kelly_stakes.values())
    race_return = 0
    
    for horse, stake in kelly_stakes.items():
        kelly_total_stake += stake
        kelly_bets += 1
        
        if horse == winner:
            # Find dividend
            for div in result.get("dividends", {}).get("WIN", []):
                if div.get("combination") == winner:
                    dividend = float(div.get("dividend", 0))
                    payout = (dividend / 10.0) * stake
                    race_return += payout
                    kelly_total_return += payout
                    kelly_wins += 1
                    break
    
    if race_return > 0:
        print(f"Race {race['race_id']}: WIN! Stake ${race_stake:.2f}, Return ${race_return:.2f}")
    else:
        print(f"Race {race['race_id']}: LOSS. Stake ${race_stake:.2f}, Winner #{winner}")

kelly_roi = ((kelly_total_return - kelly_total_stake) / kelly_total_stake * 100) if kelly_total_stake > 0 else 0

print(f"\nKelly Stakes Summary:")
print(f"  Races: {len(races)}")
print(f"  Total Bets: {kelly_bets}")
print(f"  Wins: {kelly_wins}")
print(f"  Win Rate: {kelly_wins/kelly_bets*100:.1f}%")
print(f"  Total Stake: ${kelly_total_stake:.2f}")
print(f"  Total Return: ${kelly_total_return:.2f}")
print(f"  ROI: {kelly_roi:.1f}%")

# Comparison
print("\n" + "="*60)
print("COMPARISON")
print("="*60)

print(f"\n{'Metric':<20} {'AI Top Pick':<15} {'Kelly Stakes':<15}")
print("-"*50)
print(f"{'Win Rate':<20} {top_pick_wins/len(races)*100:>13.1f}% {kelly_wins/kelly_bets*100:>13.1f}%")
print(f"{'Total Stake':<20} ${top_pick_total_stake:>12.2f} ${kelly_total_stake:>12.2f}")
print(f"{'Total Return':<20} ${top_pick_total_return:>12.2f} ${kelly_total_return:>12.2f}")
print(f"{'Profit/Loss':<20} ${top_pick_total_return-top_pick_total_stake:>12.2f} ${kelly_total_return-kelly_total_stake:>12.2f}")
print(f"{'ROI':<20} {top_pick_roi:>13.1f}% {kelly_roi:>13.1f}%")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)

if top_pick_roi > kelly_roi:
    diff = top_pick_roi - kelly_roi
    print(f"\nAI Top Pick performed BETTER by {diff:.1f}%")
    print("\nReasons:")
    print("  - Simpler strategy (one bet per race)")
    print("  - Lower total stake required")
    print("  - Focuses on highest confidence pick")
else:
    diff = kelly_roi - top_pick_roi
    print(f"\nKelly Stakes performed BETTER by {diff:.1f}%")
    print("\nReasons:")
    print("  - Diversifies across multiple horses")
    print("  - Optimizes stake sizing based on edge")
    print("  - Better bankroll management")

print("\n" + "="*60)
