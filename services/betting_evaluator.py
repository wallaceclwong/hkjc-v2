import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

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

    def evaluate_day(self, date_str: str, venue: str) -> List[Dict]:
        """Evaluates all predictions for a specific race day and returns structured data."""
        results_list = []
        
        # Look for prediction files for this date
        pattern = f"prediction_{date_str}_{venue}_R*.json"
        prediction_files = sorted(list(self.predictions_dir.glob(pattern)), key=lambda x: int(x.stem.split('_R')[-1]))

        if not prediction_files:
            return []

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
                    continue

                with open(result_file, "r", encoding="utf-8") as f:
                    result_data = json.load(f)

                # Use Kelly stake if available, otherwise unit stake
                kelly_stakes = pred_data.get("kelly_stakes", {})
                
                import re
                numbers = re.findall(r'\d+', rec_bet)
                selection = numbers[0] if numbers else ""
                
                stake = kelly_stakes.get(selection, self.unit_stake) if selection else self.unit_stake
                
                # If Kelly stake is explicitly 0, skip
                if selection in kelly_stakes and stake == 0:
                    continue

                profit_dividend = self.calculate_profit(rec_bet, result_data["dividends"])
                
                status = "WIN" if profit_dividend > 0 else "LOSS"
                status_icon = "✅" if status == "WIN" else "❌"
                
                # HKJC dividends are per $10 stake. Normalizing profit.
                gross_payout = (profit_dividend / 10.0) * stake if status == "WIN" else 0.0
                p_l = gross_payout - stake
                roi = (p_l / stake) * 100
                
                # Cloud Sync (BigQuery)
                self.bigquery.update_prediction_roi(race_id, roi, selection)

                results_list.append({
                    "race_no": race_no,
                    "race_id": race_id,
                    "result": f"{status_icon} {status}",
                    "ai_top_pick": rec_bet,
                    "kelly_stake": stake,
                    "p_l": round(p_l, 2),
                    "roi": round(roi, 1),
                    "analysis": pred_data.get("analysis_markdown", "").split('\n')[0][:80] + "..." # Snippet
                })

            except Exception as e:
                print(f"Error evaluating {pred_file.name}: {e}")

        return results_list

    def format_markdown_report(self, date_str: str, venue: str, results_list: List[Dict]) -> str:
        """Formats the results list into a pretty Markdown table with enhanced metrics."""
        if not results_list:
            return "### 📭 No data available\nNo valid results found for this meeting."
            
        total_stake = sum(r['kelly_stake'] for r in results_list)
        total_p_l = sum(r['p_l'] for r in results_list)
        total_return = total_stake + total_p_l
        overall_roi = (total_p_l / total_stake * 100) if total_stake > 0 else 0
        
        wins = sum(1 for r in results_list if "WIN" in r['result'])
        win_rate = (wins / len(results_list) * 100) if results_list else 0
        
        # Color the net profit
        p_l_color = "🟢" if total_p_l >= 0 else "🔴"
        
        report = f"# 📊 Performance Report: {date_str} ({venue})\n\n"
        
        report += "## 📈 Summary Metrics\n"
        report += f"| Metric | Value |\n"
        report += f"| :--- | :--- |\n"
        report += f"| **Total Races Bet** | {len(results_list)} |\n"
        report += f"| **Win Rate** | {win_rate:.1f}% ({wins}/{len(results_list)}) |\n"
        report += f"| **Total Stake** | ${total_stake:,.2f} |\n"
        report += f"| **Total Return** | ${total_return:,.2f} |\n"
        report += f"| **Net Profit** | {p_l_color} **${total_p_l:,.2f}** |\n"
        report += f"| **Overall ROI** | **{overall_roi:.1f}%** |\n\n"
        
        report += "## 🏁 Detailed Results Breakdown\n\n"
        report += "| Race No | AI Pick | Result of AI Pick | Kelly Stake | Result of Kelly Stake | ROI (%) | Analysis Snippet |\n"
        report += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        
        for r in results_list:
            k_stake = f"**${r['kelly_stake']:,.2f}**" if r['kelly_stake'] > 10 else f"${r['kelly_stake']:,.2f}"
            p_l_str = f"**${r['p_l']:,.2f}**" if r['p_l'] > 0 else f"${r['p_l']:,.2f}"
            
            report += f"| **R{r['race_no']}** | {r['ai_top_pick']} | {r['result']} | {k_stake} | {p_l_str} | {r['roi']}% | *{r['analysis']}* |\n"
            
        report += f"\n\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        return report

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
    parser.add_argument("--date", type=str, default="2026-03-22", help="Date in YYYY-MM-DD format")
    parser.add_argument("--venue", type=str, default="ST", help="Venue (ST or HV)")
    args = parser.parse_args()

    evaluator = BettingEvaluator()
    data = evaluator.evaluate_day(args.date, args.venue)
    report = evaluator.format_markdown_report(args.date, args.venue, data)
    print(report)
