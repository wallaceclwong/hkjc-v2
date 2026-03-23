import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add project root to path
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from services.results_ingest import ResultsIngest
from services.analytical_ingest import AnalyticalIngest
from services.odds_ingest import OddsIngest
from services.racecard_ingest import RacecardIngest
from services.barrier_trial_ingest import BarrierTrialIngest
from services.soft_data_ingest import SoftDataIngest
from services.weather_ingest import WeatherIngest
from services.schedule_ingest import fetch_monthly_schedule

async def test_8_streams(date_str, venue, race_no=1):
    logger.info(f"--- 🏁 Starting 8-Stream Diagnostic for {date_str} {venue} R{race_no} ---")
    
    results_ingest = ResultsIngest(headless=True)
    analytical_ingest = AnalyticalIngest(headless=True)
    odds_ingest = OddsIngest(headless=True)
    racecard_ingest = RacecardIngest(headless=True)
    barrier_ingest = BarrierTrialIngest(headless=True)
    soft_ingest = SoftDataIngest(headless=True)
    weather_ingest = WeatherIngest()
    
    # URL format for racecard is YYYY/MM/DD
    rc_date = date_str.replace("-", "/")

    streams = [
        ("Results", results_ingest.fetch_results, [date_str], {"venue": venue, "race_no": race_no}),
        ("Analytical", analytical_ingest.fetch_analytical_data, [date_str], {"venue": venue, "race_no": race_no}),
        ("Odds", odds_ingest.fetch_odds, [], {"race_no": race_no, "venue": venue}),
        ("Racecard", racecard_ingest.fetch_racecard, [], {"race_date_str": rc_date, "venue": venue, "race_no": race_no}),
        ("Weather", weather_ingest.fetch_current_weather, [], {}),
        ("Barrier Trials", barrier_ingest.fetch_bt_results, [date_str], {}),
        ("Soft Data (Vet)", soft_ingest.fetch_vet_records, [date_str], {"venue": venue, "race_no": race_no}),
        ("Schedule", fetch_monthly_schedule, [3, 2026], {}),
    ]

    report = []

    for name, func, args, kwargs in streams:
        logger.info(f"Testing Stream: {name}...")
        try:
            data = await func(*args, **kwargs)
            if data:
                logger.success(f"[OK] {name} stream: SUCCESS")
                report.append(f"| {name:<18} | OK      |")
            else:
                logger.error(f"[FAIL] {name} stream: FAILED (Returned None/Empty)")
                report.append(f"| {name:<18} | FAIL    |")
        except Exception as e:
            logger.exception(f"[CRASH] {name} stream: CRASHED - {e}")
            report.append(f"| {name:<18} | CRASH   |")

    # Output ASCII Report
    print("\n" + "="*45)
    print(f"       8-STREAM REPORT ({date_str})")
    print("="*45)
    print(f"| {'Stream':<18} | {'Status':<7} |")
    print("-" * 45)
    for line in report:
        print(line)
    print("="*45)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--venue", type=str, default="HV")
    parser.add_argument("--race", type=int, default=1)
    args = parser.parse_args()

    asyncio.run(test_8_streams(args.date, args.venue, args.race))
