import os
import sys
import json
from pathlib import Path
from collections import defaultdict
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def local_roi_audit():
    predictions_dir = Path("data/predictions")
    results_dir = Path("data/results")
    
    if not predictions_dir.exists():
        print("No predictions found to evaluate.")
        return

    meeting_stats = defaultdict(lambda: {"stake": 0, "profit": 0, "races": 0})
    unit_stake = 10.0

    # Get all prediction files
    pred_files = list(predictions_dir.glob("prediction_*.json"))
    print(f"Auditing {len(pred_files)} predictions locally...")

    for pred_file in pred_files:
        try:
            with open(pred_file, "r", encoding="utf-8") as f:
                pred_data = json.load(f)
            
            race_id = pred_data["race_id"]
            # Extract date and venue: 2025-04-13_ST_R11 -> 2025-04-13_ST
            parts = race_id.split("_")
            meeting_key = f"{parts[0]}_{parts[1]}"
            
            rec_bet = pred_data.get("recommended_bet", "")
            if not rec_bet or rec_bet == "NO BET":
                continue

            # Check if results exist
            result_file = results_dir / f"results_{race_id}.json"
            if not result_file.exists():
                continue

            with open(result_file, "r", encoding="utf-8") as f:
                result_data = json.load(f)

            # Calculate Profit (Minimal logic for audit)
            # Find selection
            numbers = re.findall(r'\d+', rec_bet)
            selection = numbers[0] if numbers else ""
            
            # Simple WIN/PLACE/QUINELLA check
            rec_bet_up = rec_bet.upper()
            bet_type = None
            for bt in ["WIN", "PLACE", "QUINELLA"]:
                if bt in rec_bet_up: bet_type = bt; break
            
            payout = 0.0
            if bet_type and selection:
                pool = result_data["dividends"].get(bet_type, [])
                for div in pool:
                    if div["combination"] == selection:
                        payout = float(div["dividend"])
                        break
            
            stake = pred_data.get("kelly_stakes", {}).get(selection, unit_stake)
            if stake == 0: continue

            # Normalize payout (dividends are per $10)
            gross_return = (payout / 10.0) * stake if payout > 0 else 0.0
            
            meeting_stats[meeting_key]["stake"] += stake
            meeting_stats[meeting_key]["profit"] += gross_return
            meeting_stats[meeting_key]["races"] += 1

        except Exception as e:
            continue

    if not meeting_stats:
        print("No meetings with results found.")
        return

    # Aggregate Final Stats
    total_meetings = len(meeting_stats)
    winning_meetings = 0
    losing_meetings = 0
    total_stake = 0
    total_return = 0

    for key, data in meeting_stats.items():
        net = data["profit"] - data["stake"]
        total_stake += data["stake"]
        total_return += data["profit"]
        if net > 0: winning_meetings += 1
        elif net < 0: losing_meetings += 1

    total_roi = ((total_return - total_stake) / total_stake * 100) if total_stake > 0 else 0

    print("="*60)
    print("HKJC AI PER-MEETING PERFORMANCE AUDIT (LOCAL)")
    print("="*60)
    print(f"Total Meetings Audited: {total_meetings}")
    print(f"Winning Meetings:       {winning_meetings} ({(winning_meetings/total_meetings*100):.1f}%)")
    print(f"Losing Meetings:        {losing_meetings}")
    print("-" * 30)
    print(f"Cumulative Total ROI:   {total_roi:+.2f}%")
    print(f"Average ROI/Meeting:    {(total_roi/total_meetings):+.2f}%")
    print("="*60)

if __name__ == "__main__":
    local_roi_audit()
