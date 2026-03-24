import os
# Add project root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from config.settings import Config
root_dir = Config.BASE_DIR

preds_dir = Path(root_dir) / "data" / "predictions"
results_dir = Path(root_dir) / "data" / "results"

total_staked = 0.0
total_returned = 0.0
wins = 0
total_bets = 0

if not preds_dir.exists() or not results_dir.exists():
    print("No data found.")
    sys.exit(0)

for pref in sorted(preds_dir.glob("prediction_*.json")):
    try:
        with open(pref, "r", encoding="utf-8") as f:
            pred_data = json.load(f)
        
        race_id = pred_data.get("race_id", "")
        if not race_id: continue
            
        res_file = results_dir / f"results_{race_id}.json"
        if not res_file.exists():
            continue
            
        with open(res_file, "r", encoding="utf-8") as f:
            res_data = json.load(f)
            
        rec_bet = pred_data.get("recommended_bet", "")
        if "WIN" not in rec_bet:
            continue
            
        # find selection using same fast regex implementation
        import re
        numbers = re.findall(r'\d+', rec_bet)
        selection = numbers[0] if numbers else ""
        if not selection: continue
        
        # Check if Kelly triggered
        kelly_stake = pred_data.get("kelly_stakes", {}).get(selection, 0)
        if kelly_stake == 0:
            continue
            
        # Enforce $10 flat bet
        stake = 10.0
        total_staked += stake
        total_bets += 1
        
        # parse payouts correctly
        payout = 0.0
        won = False
        pool = res_data.get("dividends", {}).get("WIN", [])
        for div in pool:
            if str(div.get("combination", "")) == selection:
                payout = float(div.get("dividend", 0))
                won = True
                break
                
        if won:
            # Payouts in HKJC are calculated per $10 unit
            returns = (stake / 10.0) * payout
            total_returned += returns
            wins += 1
            
    except Exception as e:
        continue

print(f"Total Races Bet (Edge Found): {total_bets}")
print(f"Total Staked: ${total_staked:.2f}")
print(f"Total Returned: ${total_returned:.2f}")
net_profit = total_returned - total_staked
print(f"Gross Profit: ${net_profit:.2f}")

if total_staked > 0:
    roi = (net_profit / total_staked) * 100
    print(f"FLAT $10 ROI: {roi:.2f}%")
else:
    print("ROI: 0.00%")

if total_bets > 0:
    win_rate = (wins / total_bets) * 100
    print(f"AI Hit Rate: {win_rate:.2f}%")
