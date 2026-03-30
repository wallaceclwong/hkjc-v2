import asyncio
import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import RaceCard, HorseEntry
from services.browser_manager import BrowserManager

class RacecardIngest:
    def __init__(self, headless=True, browser_mgr=None):
        self.headless = headless
        self.browser_mgr = browser_mgr or BrowserManager(headless=headless)

    async def fetch_racecard(self, date_str: str, venue: str, race_no: int, page=None) -> Optional[RaceCard]:
        """
        Fetches racecard data from HKJC website.
        date_str: YYYY/MM/DD or YYYY-MM-DD
        venue: ST or HV
        race_no: int
        """
        formatted_date = date_str.replace("-", "/")
        dt_iso = date_str.replace("/", "-")
        url = f"https://bet.hkjc.com/en/racing/home/{formatted_date}/{venue}/{race_no}"
        
        own_page = False
        context = None
        if not page:
            # use persistent context to avoid bot detection
            context, page = await self.browser_mgr.get_persistent_context("ingest")
            own_page = True
            
        try:
            print(f"[RACECARD] Navigating to {url}...")
            await page.goto(url, wait_until="load", timeout=90000)
            
            # Wait for any of the known table selectors
            table_selectors = ["table.starter", "table.table_bd.racecard", "#racecardlist table"]
            table_found = False
            for sel in table_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=10000)
                    print(f"[RACECARD] Found horse table with selector: {sel}")
                    table_found = True
                    break
                except:
                    continue
            
            if not table_found:
                # Last ditch: look for any table with "Horse No."
                tables = await page.query_selector_all("table")
                for t in tables:
                    text = await t.inner_text()
                    if "Horse No." in text and "Jockey" in text:
                        print("[RACECARD] Found horse table by text content analysis.")
                        table_found = True
                        break
            
            if not table_found:
                raise Exception("Could not locate horse table on page.")

            # --- Base Race Info ---
            content_text = await page.inner_text("#innerContent, .p_line, body")
            
            distance = 1200
            track_type = "Turf"
            course = "A"
            race_class = "Class 4"

            # Parse Distance info
            dist_match = re.search(r'(\d+)M', content_text)
            if dist_match:
                distance = int(dist_match.group(1))
            
            if "All Weather" in content_text or "AWT" in content_text:
                track_type = "All Weather Track"
            elif "Turf" in content_text:
                track_type = "Turf"

            # Parse Class/Rating
            class_match = re.search(r'(Class \d|Griffin|Group \d)', content_text)
            if class_match:
                race_class = class_match.group(1)

            # --- Horse Table Extraction ---
            # We look for rows that have horse data
            rows = await page.query_selector_all("tr.f_tac, table.starter tr, table.table_bd.racecard tr")
            
            horses = []
            seen_saddles = set()
            
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) < 13:
                    continue
                
                saddle_text = (await cols[0].inner_text()).strip()
                if not saddle_text.isdigit():
                    continue
                
                saddle_number = int(saddle_text)
                if saddle_number in seen_saddles:
                    continue # Skip duplicates if selectors overlapped
                
                # Column 2: Last 6 Runs
                last_6_raw = (await cols[1].inner_text()).strip()
                last_6 = [r.strip() for r in last_6_raw.split('/') if r.strip()]

                # Column 4: Horse Info
                horse_link = await cols[3].query_selector("a")
                if not horse_link:
                    continue
                
                horse_name = (await horse_link.inner_text()).strip()
                href = await horse_link.get_attribute("href")
                
                horse_id = horse_name # Fallback
                id_match = re.search(r'horseid=([^&]+)', href)
                if id_match:
                    horse_id = id_match.group(1)
                
                # Weight (Col 5)
                wt_text = (await cols[4].inner_text()).strip()
                try:
                    weight = float(wt_text)
                except:
                    weight = 133.0
                
                # Jockey (Col 6)
                jockey = (await cols[5].inner_text()).strip()
                
                # Draw (Col 7)
                draw_text = (await cols[6].inner_text()).strip()
                try:
                    draw = int(draw_text)
                except:
                    draw = 0
                
                # Trainer (Col 8)
                trainer = (await cols[7].inner_text()).strip()
                
                # Gear (Col 13)
                gear = (await cols[12].inner_text()).strip()
                
                # Owner (Col 14)
                owner = (await cols[13].inner_text()).strip() if len(cols) > 13 else ""

                entry = HorseEntry(
                    horse_id=horse_id,
                    horse_name=horse_name,
                    owner=owner,
                    saddle_number=saddle_number,
                    draw=draw,
                    jockey=jockey,
                    trainer=trainer,
                    weight=weight,
                    last_6_runs=last_6,
                    gear=gear
                )
                horses.append(entry)
                seen_saddles.add(saddle_number)

            if not horses:
                print(f"[ERROR] No horses found for R{race_no}.")
                if own_page: await page.close()
                return None

            race_id = f"{dt_iso}_{venue}_R{race_no}"
            
            card = RaceCard(
                race_id=race_id,
                date=datetime.strptime(dt_iso, "%Y-%m-%d"),
                race_number=race_no,
                distance=distance,
                track_type=track_type,
                course=course,
                race_class=race_class,
                horses=horses
            )
            
            print(f"[RACECARD] Successfully scraped {len(horses)} horses for {race_id}")
            if own_page:
                await page.close()
            return card
            
        except Exception as e:
            print(f"[RACECARD] Extraction ERROR: {e}")
            if page:
                try:
                    debug_path = f"tmp/racecard_error_R{race_no}.png"
                    await page.screenshot(path=debug_path)
                    print(f"[RACECARD] Saved debug screenshot to {debug_path}")
                except: pass
            if own_page:
                await page.close()
            return None

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="HKJC Racecard Ingestor")
    parser.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--venue", type=str, default="ST", help="ST or HV")
    parser.add_argument("--race", type=int, default=1)
    args = parser.parse_args()

    ingest = RacecardIngest(headless=True)
    card = await ingest.fetch_racecard(args.date, args.venue, args.race)
    if card:
        os.makedirs("data", exist_ok=True)
        date_clean = args.date.replace("-", "")
        filename = f"data/racecard_{date_clean}_R{args.race}.json"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(card.model_dump_json(indent=2))
        print(f"Racecard saved to {filename}")
    else:
        print("Scrape FAILED.")
    
    await ingest.browser_mgr.stop()

if __name__ == "__main__":
    asyncio.run(main())
