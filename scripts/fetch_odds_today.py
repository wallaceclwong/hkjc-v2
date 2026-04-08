"""Fetch live odds for today's races and update prediction files."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.odds_ingest import OddsIngest

DATE = "2026-04-06"
VENUE = "ST"
MAX_RACES = 11
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


async def main():
    ingest = OddsIngest(headless=True)
    all_odds = {}

    for r in range(1, MAX_RACES + 1):
        close = (r == MAX_RACES)
        result = await ingest.fetch_odds(DATE, race_no=r, venue=VENUE, close_browser=close)
        if result and result.get("win_odds"):
            all_odds[r] = result["win_odds"]
            print(f"R{r}: {result['win_odds']}")
        else:
            print(f"R{r}: no odds available")

    if not all_odds:
        print("No odds fetched. Exiting.")
        return

    # Update prediction files with fresh odds
    pred_dir = DATA_DIR / "predictions"
    updated = 0
    for r, odds in all_odds.items():
        pred_file = pred_dir / f"prediction_{DATE}_{VENUE}_R{r}.json"
        if pred_file.exists():
            with open(pred_file, "r", encoding="utf-8") as f:
                pred = json.load(f)
            pred["market_odds"] = {str(k): v for k, v in odds.items()}
            with open(pred_file, "w", encoding="utf-8") as f:
                json.dump(pred, f, indent=2)
            print(f"Updated prediction file for R{r}")
            updated += 1

    print(f"\nDone. Updated {updated} prediction files with live odds.")


if __name__ == "__main__":
    asyncio.run(main())
