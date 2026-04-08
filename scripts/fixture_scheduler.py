"""
Smart Fixture Scheduler
========================
Fetches HKJC seasonal fixtures and auto-schedules prediction jobs.

Usage:
    python scripts/fixture_scheduler.py --fetch
    python scripts/fixture_scheduler.py --schedule
"""
import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_FILE = PROJECT_ROOT / "data" / "fixtures_season.json"

# Meeting type schedule configuration
SCHEDULE_CONFIG = {
    "D": {  # Day meetings (Sha Tin)
        "scrape_time": "07:00",      # Early morning racecard scrape
        "predict_time": "09:00",     # Morning predictions
        "description": "Day Meeting - Sha Tin"
    },
    "N": {  # Night meetings (Happy Valley)
        "scrape_time": "16:00",      # Afternoon racecard scrape
        "predict_time": "18:00",     # Evening predictions
        "description": "Night Meeting - Happy Valley"
    }
}

def fetch_fixtures():
    """Fetch fixtures from HKJC website using existing scraper."""
    print("[INFO] Fetching seasonal fixtures from HKJC...")
    
    # Use existing racecard scraper to get fixtures
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://bet.hkjc.com/racing/info/Info/Meeting/English/Local/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse fixture data from the page
        fixtures = []
        # Add parsing logic here based on HKJC page structure
        
        print(f"[INFO] Fetched {len(fixtures)} fixtures")
        return fixtures
    except Exception as e:
        print(f"[ERROR] Failed to fetch fixtures: {e}")
        return []

def load_fixtures():
    """Load existing fixtures."""
    if FIXTURES_FILE.exists():
        with open(FIXTURES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def parse_date(date_str):
    """Parse HKJC date format."""
    return datetime.strptime(date_str, "%d/%m/%Y")

def get_upcoming_meetings(fixtures, days_ahead=7):
    """Get upcoming meetings for next N days."""
    today = datetime.now().date()
    upcoming = []
    
    for fixture in fixtures:
        meeting_date = parse_date(fixture["date"]).date()
        if today <= meeting_date <= (today + timedelta(days=days_ahead)):
            upcoming.append(fixture)
    
    return sorted(upcoming, key=lambda x: parse_date(x["date"]))

def schedule_predictions(meeting_date, venue, meeting_type):
    """Schedule Windows tasks for a meeting."""
    config = SCHEDULE_CONFIG.get(meeting_type, SCHEDULE_CONFIG["D"])
    
    # Format date for schtasks: DD/MM/YYYY -> MM/DD/YYYY
    dt = parse_date(meeting_date)
    sch_date = dt.strftime("%m/%d/%Y")
    date_iso = dt.strftime('%Y-%m-%d')
    date_compact = dt.strftime('%Y%m%d')
    
    # Task names
    scrape_task = f"HKJC_Auto_Scrape_{venue}_{date_compact}"
    predict_task = f"HKJC_Auto_Predict_{venue}_{date_compact}"
    
    python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    
    # Create scrape task
    scrape_cmd = (
        f'schtasks /create /tn "{scrape_task}" '
        f'/tr "\\"{python_exe}\\" \"{PROJECT_ROOT}\\scripts\\pc_race_day.py\" --date {date_iso} --venue {venue}" '
        f'/sc once /st {config["scrape_time"]} /sd {sch_date} /f'
    )
    
    # Create prediction task (runs after scrape)
    predict_cmd = (
        f'schtasks /create /tn "{predict_task}" '
        f'/tr "\\"{python_exe}\\" \"{PROJECT_ROOT}\\scripts\\vm_predict.py\" --date {date_iso} --venue {venue}" '
        f'/sc once /st {config["predict_time"]} /sd {sch_date} /f'
    )
    
    try:
        subprocess.run(scrape_cmd, shell=True, check=True, capture_output=True)
        print(f"[✓] Scheduled racecard scrape: {meeting_date} {config['scrape_time']}")
        
        subprocess.run(predict_cmd, shell=True, check=True, capture_output=True)
        print(f"[✓] Scheduled predictions: {meeting_date} {config['predict_time']}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"[✗] Failed to schedule: {e}")
        return False

def auto_schedule():
    """Auto-schedule upcoming meetings."""
    fixtures = load_fixtures()
    if not fixtures:
        print("[ERROR] No fixtures loaded. Run with --fetch first.")
        return
    
    upcoming = get_upcoming_meetings(fixtures, days_ahead=14)
    print(f"[INFO] Found {len(upcoming)} upcoming meetings")
    
    for meeting in upcoming:
        date_str = meeting["date"]
        venue = meeting["venue"]
        mtype = meeting.get("type", "D")
        
        print(f"\n[Scheduling] {date_str} - {venue} ({mtype})")
        schedule_predictions(date_str, venue, mtype)
    
    print("\n[✓] Auto-scheduling complete!")

def generate_cron_schedule():
    """Generate cron-like schedule for documentation."""
    fixtures = load_fixtures()
    upcoming = get_upcoming_meetings(fixtures, days_ahead=30)
    
    print("\n=== HKJC Meeting Schedule ===\n")
    
    for meeting in upcoming:
        date_str = meeting["date"]
        venue = meeting["venue"]
        mtype = meeting.get("type", "D")
        config = SCHEDULE_CONFIG.get(mtype, SCHEDULE_CONFIG["D"])
        
        dt = parse_date(date_str)
        print(f"{dt.strftime('%a %d %b %Y')}: {venue} ({config['description']})")
        print(f"  - Racecard scrape: {config['scrape_time']}")
        print(f"  - Predictions: {config['predict_time']}")
        print()
    
    return upcoming

def main():
    parser = argparse.ArgumentParser(description="HKJC Fixture Scheduler")
    parser.add_argument("--fetch", action="store_true", help="Fetch latest fixtures")
    parser.add_argument("--schedule", action="store_true", help="Schedule upcoming meetings")
    parser.add_argument("--list", action="store_true", help="List upcoming meetings")
    
    args = parser.parse_args()
    
    if args.fetch:
        fixtures = fetch_fixtures()
        if fixtures:
            with open(FIXTURES_FILE, "w", encoding="utf-8") as f:
                json.dump(fixtures, f, indent=2)
            print(f"[✓] Saved {len(fixtures)} fixtures")
    
    elif args.schedule:
        auto_schedule()
    
    elif args.list:
        generate_cron_schedule()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
