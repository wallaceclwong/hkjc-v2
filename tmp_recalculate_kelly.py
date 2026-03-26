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

    pred_path = Path("data/predictions/prediction_2026-03-25_HV_R1.json")
    if not pred_path.exists():
        print(f"File not found: {pred_path}")
        return

    with open(pred_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    probs = data.get("probabilities", {})
    odds = data.get("market_odds", {})

    print(f"Recalculating Kelly for {data['race_id']}...")
    print(f"Bankroll: {Config.INITIAL_BANKROLL}, Fraction: {Config.KELLY_FRACTION}")

    stakes = kelly.calculate_race_stakes(probs, odds)
    
    print("Calculated Stakes:")
    for horse, stake in stakes.items():
        print(f"  Horse {horse}: ${stake} (Prob: {probs.get(horse):.2f}, Odds: {odds.get(horse)})")

    data["kelly_stakes"] = stakes
    
    # Save back to verify
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated file successfully.")

if __name__ == "__main__":
    main()
