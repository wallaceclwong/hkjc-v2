from google.cloud import bigquery
from config.settings import Config
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_roi_audit():
    client = bigquery.Client(project=Config.PROJECT_ID)
    query = f"""
        SELECT 
            date, 
            SUM(roi) as daily_roi,
            COUNT(*) as race_count,
            AVG(confidence_score) as avg_conf
        FROM `{Config.PROJECT_ID}.hkjc_dw.ai_predictions`
        GROUP BY date
        ORDER BY date DESC
    """
    
    try:
        query_job = client.query(query)
        rows = list(query_job.result())
        
        if not rows:
            print("No prediction data found in BigQuery yet.")
            return

        total_meetings = len(rows)
        winning_meetings = 0
        losing_meetings = 0
        flat_meetings = 0
        total_roi = 0.0

        for row in rows:
            roi = row.daily_roi or 0.0
            total_roi += roi
            if roi > 0:
                winning_meetings += 1
            elif roi < 0:
                losing_meetings += 1
            else:
                flat_meetings += 1
        
        win_rate = (winning_meetings / total_meetings) * 100 if total_meetings > 0 else 0
        avg_roi = total_roi / total_meetings if total_meetings > 0 else 0

        print("="*60)
        print("HKJC AI PER-MEETING PERFORMANCE AUDIT")
        print("="*60)
        print(f"Total Meetings Audited: {total_meetings}")
        print(f"Winning Meetings:       {winning_meetings} ({win_rate:.1f}%)")
        print(f"Losing Meetings:        {losing_meetings}")
        print(f"Flat/No-Bet Meetings:   {flat_meetings}")
        print("-" * 30)
        print(f"Cumulative Total ROI:   {total_roi:+.2f}%")
        print(f"Avg ROI per Meeting:    {avg_roi:+.2f}%")
        print("="*60)
        
        print("\nRECENT PERFORMANCE:")
        for row in rows[:5]:
            print(f"Date: {row.date} | ROI: {row.daily_roi:+.2f}% | Races: {row.race_count}")
        
    except Exception as e:
        print(f"Audit failed: {e}")

if __name__ == "__main__":
    run_roi_audit()
