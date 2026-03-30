import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter
from loguru import logger

from dashboard.dependencies import (
    DATA_DIR, USE_FIRESTORE, firestore, get_latest_file, 
    get_local_ip, load_horse_names, Config,
    get_current_meeting_info
)
from services.meeting_settlement import MeetingSettlement

router = APIRouter(prefix="/execution")

class BetRequest(BaseModel):
    date: str
    venue: str
    race: int
    selection: str
    stake: float

@router.get("/recommendations")
async def get_recommendations():
    """Returns predictions with Kelly stakes for the next meeting."""
    try:
        target_date = datetime.now().strftime("%Y-%m-%d")
        preds = list((DATA_DIR / "predictions").glob(f"prediction_{target_date}_*.json"))
        recommendations = []
        for p_file in preds:
            with open(p_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("is_best_bet") or data.get("recommended_bet"):
                    recommendations.append(data)
        
        return {"success": True, "recommendations": recommendations}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/stage_bet")
async def stage_bet(request: BetRequest):
    """Triggers the ExecutionEngine to stage a bet."""
    try:
        asyncio.create_task(
            execution_engine.prepare_bet_slip(
                request.date, 
                request.venue, 
                request.race, 
                request.selection, 
                request.stake
            )
        )
        return {"success": True, "message": f"Execution started for Race {request.race} selection {request.selection}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/recalibrate")
async def recalibrate():
    """Triggers the RLOptimizer to adjust biases based on recent performance."""
    try:
        rl_optimizer.optimize_from_past_days(days=7)
        biases = rl_optimizer.load_biases()
        return {"success": True, "message": "Recalibration complete.", "biases": biases}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/force_update")
async def force_update():
    """Triggers a full re-ingestion and re-prediction cycle via daily_runner.py."""
    try:
        target_date = datetime.now().strftime("%Y-%m-%d") 
        log_file = DATA_DIR / "force_update.log"
        script_path = BASE_DIR / "services" / "daily_runner.py"
        
        single_cmd = [
            sys.executable, str(script_path), 
            "--date", target_date,
            "--race", "1" 
        ]
        
        subprocess.run(single_cmd, capture_output=True, cwd=str(BASE_DIR))

        full_cmd = [sys.executable, str(script_path), "--date", target_date]
        with open(log_file, "a") as f:
            subprocess.Popen(full_cmd, stdout=f, stderr=f, cwd=str(BASE_DIR))
            
        return {
            "success": True, 
            "message": f"Race 1 updated immediately. Full meeting re-analysis is continuing in the background.",
            "log": str(log_file)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/settle")
async def settle_meeting(request: dict):
    """Triggers the MeetingSettlement orchestrator for a specific date and venue."""
    try:
        date = request.get("date")
        venue = request.get("venue")
        
        if not date or not venue:
            return {"success": False, "error": "Missing date or venue"}
            
        async def run_settlement():
            logger.info(f"🚀 Dashboard-triggered settlement for {date} ({venue})")
            settlement = MeetingSettlement(headless=True)
            await settlement.settle_meeting(date, venue)
            
        asyncio.create_task(run_settlement())
        
        return {
            "success": True, 
            "message": f"Settlement process started for {date} ({venue}). It will take ~2 minutes."
        }
    except Exception as e:
        logger.error(f"Settlement failed: {e}")
        return {"success": False, "error": str(e)}

@router.get("/kelly_settings")
async def get_kelly_settings():
    """Returns current Kelly Criterion settings."""
    return {
        "success": True,
        "bankroll": Config.INITIAL_BANKROLL,
        "fraction": Config.KELLY_FRACTION
    }

@router.post("/kelly_settings")
async def update_kelly_settings(settings: dict):
    """Updates Kelly Criterion settings (in-memory for current session)."""
    if "bankroll" in settings:
        Config.INITIAL_BANKROLL = float(settings["bankroll"])
    if "fraction" in settings:
        Config.KELLY_FRACTION = float(settings["fraction"])
    return {"success": True, "message": "Kelly settings updated for current session."}
from fastapi import APIRouter, Header

@router.get("/trigger/watchdog")
async def trigger_watchdog(x_cloud_scheduler: str = Header(None)):
    """
    Stateless trigger for Market Watchdog.
    Meant to be called by Google Cloud Scheduler every 2-5 minutes.
    """
    # Simple security check (Cloud Scheduler can send custom headers)
    if not x_cloud_scheduler and not Config.DEBUG:
        return {"success": False, "error": "Unauthorized. Missing trigger header."}

    try:
        meeting_date, venue = get_current_meeting_info()
        max_races = 11 if venue == "ST" else 9
        
        logger.info(f"Triggering Watchdog sweep for {meeting_date} ({venue}) — {max_races} races")
        
        results = []
        fail_count = 0
        for r in range(1, max_races + 1):
            try:
                alerts = await market_watchdog.poll_and_detect(r, venue)
                results.append({"race": r, "alerts": len(alerts), "status": "OK"})
            except Exception as e:
                logger.error(f"Watchdog failed for Race {r}: {e}")
                results.append({"race": r, "error": str(e), "status": "FAIL"})
                fail_count += 1
        
        # Proper Alerting Integration: Log a specific pattern for GCP
        if fail_count > (max_races / 2):
            logger.critical(f"❌ CRITICAL: Scraper Partial Failure! {fail_count}/{max_races} races failed to poll.")
            
        return {
            "success": True, 
            "meeting": f"{meeting_date}_{venue}",
            "sweep_results": results,
            "fail_count": fail_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Watchdog trigger failed: {e}")
        return {"success": False, "error": str(e)}
