import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from services.odds_ingest import OddsIngest
from services.browser_manager import BrowserManager

class MarketWatchdog:
    def __init__(self, drop_threshold=0.20):
        """
        drop_threshold: Decimal percentage drop to trigger a 'Smart Money' alert.
        Default is 20% drop.
        """
        self.odds_service = OddsIngest(headless=True)
        self.baselines = {} # {race_id: {horse_no: baseline_odds}}
        self.drop_threshold = drop_threshold
        self.data_dir = Config.BASE_DIR / "data/alerts"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.last_heartbeat = None

    async def poll_and_detect(self, race_no: int, venue: str = "ST"):
        """
        Polls current odds and detects significant drops compared to baseline.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        race_id = f"{date_str}_{venue}_R{race_no}"
        
        try:
            logger.info(f"Watchdog polling {race_id}...")
            odds_data = await self.odds_service.fetch_odds(date_str=date_str, race_no=race_no, venue=venue)
            
            if not odds_data:
                logger.warning(f"Watchdog failed to fetch odds for {race_id}")
                return []
            
            self.last_heartbeat = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error in poll_and_detect for {race_id}: {e}")
            return []

        current_win_odds = odds_data.get("win_odds", {})
        alerts = []

        # If we don't have a baseline for this race yet, set it now
        if race_id not in self.baselines:
            self.baselines[race_id] = current_win_odds
            logger.info(f"Baseline set for {race_id}")
            return []

        baseline_win_odds = self.baselines[race_id]

        for horse_no, current_val in current_win_odds.items():
            baseline_val = baseline_win_odds.get(horse_no)
            
            if baseline_val and current_val < baseline_val:
                drop_pct = (baseline_val - current_val) / baseline_val
                
                if drop_pct >= self.drop_threshold:
                    logger.warning(f"🔥 SMART MONEY DETECTED: Race {race_no} Horse {horse_no} dropped {drop_pct*100:.1f}% ({baseline_val} -> {current_val})")
                    
                    alert = {
                        "type": "SMART MONEY",
                        "severity": "high",
                        "horse_no": horse_no,
                        "description": f"Significant odds drop detected: ${baseline_val} to ${current_val} ({drop_pct*100:.1f}% drop).",
                        "implied_prob_change": round((1/current_val - 1/baseline_val) * 100, 2),
                        "timestamp": datetime.now().isoformat()
                    }
                    alerts.append(alert)

        if alerts:
            self._save_alerts(race_id, alerts)
            
        return alerts

    def _save_alerts(self, race_id: str, alerts: List[Dict]):
        alert_file = self.data_dir / f"market_alerts_{race_id}.json"
        
        # Load existing if any
        existing = []
        if alert_file.exists():
            try:
                with open(alert_file, "r", encoding="utf-8") as f:
                    existing = json.load(f).get("alerts", [])
            except: pass

        # Combine and deduplicate by horse_no (keep latest)
        combined = {a["horse_no"]: a for a in (existing + alerts)}
        
        with open(alert_file, "w", encoding="utf-8") as f:
            json.dump({
                "race_id": race_id,
                "updated_at": datetime.now().isoformat(),
                "alerts": list(combined.values())
            }, f, indent=2)

    async def run_loop(self, race_no: int, venue: str = "ST", interval=120):
        """
        Continuous background loop for a specific race.
        """
        logger.info(f"Starting Watchdog loop for Race {race_no} every {interval}s")
        while True:
            try:
                await self.poll_and_detect(race_no, venue)
            except Exception as e:
                logger.error(f"CRITICAL: Watchdog loop error for Race {race_no}: {e}")
            await asyncio.sleep(interval)

if __name__ == "__main__":
    # Test script
    watchdog = MarketWatchdog(drop_threshold=0.1) # 10% for testing
    asyncio.run(watchdog.poll_and_detect(1, "ST"))
