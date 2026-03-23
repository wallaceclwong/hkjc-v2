import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from services.bigquery_service import BigQueryService

class BettingEvaluator:
    def __init__(self):
        self.results_dir = Path("data/results")
        self.predictions_dir = Path("data/predictions")
        self.unit_stake = 10.0  # Default $10 unit stake for calculations
        self.bigquery = BigQueryService()

    def evaluate_day(self, date_str: str, venue: str):
        """Evaluates all predictions for a specific race day."""
        print(f"\n===== Performance Report: {date_str} ({venue}) =====")
        print(f"{'Race':<6} | {'Bet':<15} | {'Result':<10} | {'P&L ($)':<10} | {'ROI (%)':<10}")
        print("-" * 65)

        total_stake = 0
        total_profit = 0
        races_evaluated = 0

        # Look for prediction files for this date
        pattern = f"prediction_{date_str}_{venue}_R*.json"
        prediction_files = sorted(list(self.predictions_dir.glob(pattern)), key=lambda x: int(x.stem.split('_R')[-1]))

        if not prediction_files:
            print(f"No predictions found for {date_str}")
            return

        for pred_file in prediction_files:
            try:
                with open(pred_file, "r", encoding="utf-8") as f:
                    pred_data = json.load(f)
                
                race_id = pred_data["race_id"]
                race_no = race_id.split("_R")[-1]
                rec_bet = pred_data.get("recommended_bet", "")
                
                if not rec_bet or rec_bet == "NO BET":
                    continue

                # Load results
                result_file = self.results_dir / f"results_{race_id}.json"
                if not result_file.exists():
                    # print(f"  R{race_no}: Result data missing.")
                    continue

                with open(result_file, "r", encoding="utf-8") as f:
                    result_data = json.load(f)

                # Use Kelly stake if available, otherwise unit stake
                probabilities = pred_data.get("probabilities", {})
                kelly_stakes = pred_data.get("kelly_stakes", {})
                
                # Check if the recommended bet has a specific Kelly stake
                # Recommended bet might be "WIN 5", so we extract "5"
                import re
                numbers = re.findall(r'\d+', rec_bet)
                selection = numbers[0] if numbers else ""
                
                stake = kelly_stakes.get(selection, self.unit_stake) if selection else self.unit_stake
                
                # If Kelly stake is explicitly 0, skip
                if selection in kelly_stakes and stake == 0:
                    continue

                profit_dividend = self.calculate_profit(rec_bet, result_data["dividends"])
                
                status = "WIN" if profit_dividend > 0 else "LOSS"
                
                # HKJC dividends are per $10 stake. Normalizing profit.
                gross_payout = (profit_dividend / 10.0) * stake if status == "WIN" else 0.0
                p_l = gross_payout - stake
                roi = (p_l / stake) * 100
                
                # Cloud Sync (BigQuery)
                self.bigquery.update_prediction_roi(race_id, roi, selection)

                print(f"R{race_no:<5} | {rec_bet:<15} | {status:<10} | {p_l:<10.2f} | {roi:<10.1f}%")

                total_stake += stake
                total_profit += gross_payout
                races_evaluated += 1

            except Exception as e:
                print(f"Error evaluating {pred_file.name}: {e}")

        if races_evaluated > 0:
            net_p_l = total_profit - total_stake
            overall_roi = (net_p_l / total_stake) * 100
            print("-" * 65)
            print(f"SUMMARY: {races_evaluated} Races | Stake: ${total_stake:.0f} | Return: ${total_profit:.2f} | Net: ${net_p_l:.2f}")
            print(f"TOTAL ROI: {overall_roi:.1f}%")
        else:
            print("No valid races with both predictions and results found.")

    def calculate_profit(self, rec_bet: str, dividends: Dict[str, Any]) -> float:
        """
        Calculates the gross payout for a specific bet.
        Handles variations like "WIN 9", "WIN - Horse 5", "QUINELLA 3-10"
        """
        import re
        
        # Clean the string and find the bet type
        rec_bet_up = rec_bet.upper()
        bet_type = None
        for bt in ["WIN", "PLACE", "QUINELLA"]:
            if bt in rec_bet_up:
                bet_type = bt
                break
        
        if not bet_type:
            return 0.0

        # Extract all numbers from the string
        numbers = re.findall(r'\d+', rec_bet)
        if not numbers:
            return 0.0

        # Handle WIN / PLACE payouts
        if bet_type in ["WIN", "PLACE"]:
            selection = numbers[0]
            pool = dividends.get(bet_type, [])
            for div in pool:
                if div["combination"] == selection:
                    return float(div["dividend"])
        
        # Handle QUINELLA (e.g., "QUINELLA 3-10")
        elif bet_type == "QUINELLA":
            pool = dividends.get("QUINELLA", [])
            # Take the first two numbers found
            if len(numbers) < 2: return 0.0
            sel_parts = sorted([numbers[0], numbers[1]])
            
            for div in pool:
                div_parts = sorted(div["combination"].split(","))
                if sel_parts == div_parts:
                    return float(div["dividend"])

        return 0.0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate Betting Performance")
    parser.add_argument("--date", type=str, default="2026-03-15", help="Date in YYYY-MM-DD format")
    parser.add_argument("--venue", type=str, default="ST", help="Venue (ST or HV)")
    args = parser.parse_args()

    evaluator = BettingEvaluator()
    evaluator.evaluate_day(args.date, args.venue)
