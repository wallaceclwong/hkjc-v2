import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from services.prediction_engine import KellyCriterion
from config.settings import Config

def main():
    kelly = KellyCriterion(
        bankroll=Config.INITIAL_BANKROLL,
        fractional_kelly=Config.KELLY_FRACTION
    )

    pred_dir = Path("data/predictions")
    if not pred_dir.exists():
        print(f"Directory not found: {pred_dir}")
        return

    updated_count = 0
    skipped_count = 0

    for pred_path in pred_dir.glob("prediction_*.json"):
        with open(pred_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                continue

        probs = data.get("probabilities", {})
        odds = data.get("market_odds", {})
        existing_stakes = data.get("kelly_stakes", {})

        if probs and odds and (not existing_stakes or existing_stakes == {}):
            stakes = kelly.calculate_race_stakes(probs, odds)
            if stakes:
                data["kelly_stakes"] = stakes
                with open(pred_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                updated_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1

    print(f"Batch update complete. Updated: {updated_count}, Skipped/No Bets: {skipped_count}")

if __name__ == "__main__":
    main()
