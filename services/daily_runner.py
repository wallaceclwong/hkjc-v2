import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add project root for direct imports in settlement step
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_fixtures(date_str=None):
    """
    Loads fixture data. Automatically selects the correct year-based fixture file.
    """
    base_dir = Path(__file__).resolve().parent.parent / "data"
    year = None
    if date_str:
        try:
            year = datetime.strptime(date_str, "%Y-%m-%d").year
        except:
            pass
    if year:
        year_fixture = base_dir / f"fixtures_{year}.json"
        if year_fixture.exists():
            with open(year_fixture, "r", encoding="utf-8") as f:
                return json.load(f)
    for fallback in ["march_2026_fixtures.json", "fixtures_2026.json"]:
        p = base_dir / fallback
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

def run_ingestion(script_path, date, venue, race_no, timeout=180):
    """Runs a single ingestion step as a subprocess."""
    cmd = [sys.executable, script_path, "--date", date, "--venue", venue, "--race", str(race_no)]
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            print(f"[WARN] {script_path} R{race_no} exited {result.returncode}: {result.stderr[:200]}")
        else:
            print(result.stdout.strip()[:300])
        return race_no, result.returncode == 0
    except Exception as e:
        print(f"[ERROR] {script_path} R{race_no}: {e}")
        return race_no, False

def detect_race_count(venue: str, date_str: str) -> int:
    date_compact = date_str.replace("-", "")
    data_dir = Path("data")
    existing = list(data_dir.glob(f"racecard_{date_compact}_R*.json"))
    if existing:
        return max(int(p.stem.split("_R")[-1]) for p in existing)
    return 10 if venue == "ST" else 9

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HKJC Master Orchestrator")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--venue", type=str, default=None)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--race", type=int, default=None)
    args = parser.parse_args()

    fixtures = load_fixtures(date_str=args.date)
    target_dt = datetime.strptime(args.date, "%Y-%m-%d")
    target_str = target_dt.strftime("%d/%m/%Y")
    is_future = target_dt.date() > datetime.now().date()
    
    today_race_days = [f for f in fixtures if f["date"] == target_str]
    if not today_race_days:
        print(f"No races scheduled for {args.date}.")
        return

    services_dir = Path(__file__).resolve().parent
    for race_day in today_race_days:
        venue = args.venue or race_day["venue"]
        max_races = detect_race_count(venue, args.date)
        races_to_run = [args.race] if args.race else range(1, max_races + 1)
        
        print(f"\nProcessing race day: {args.date} at {venue}")

        # 0. Weather Intelligence (UNIFIED ENGINE)
        print(f"\n--- Generating Unified Weather Intelligence for {venue} ---")
        run_ingestion(str(services_dir / "generate_weather_intel.py"), args.date, venue, 1)

        # 1. Racecard ingestion
        print(f"\n--- Ingesting Racecards ---")
        run_ingestion(str(services_dir / "racecard_ingest.py"), args.date.replace("-", "/"), venue, races_to_run[0]) # Simplified for restore

    print("\nDaily run complete.")

if __name__ == "__main__":
    main()
