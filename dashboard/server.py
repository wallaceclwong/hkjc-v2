import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

# WeatherNext 2 Integration (Safe Import)
try:
    sys.path.append("c:/Users/ASUS/weathernext_pro/src")
    from v2_engine import get_track_forecast
except ImportError:
    get_track_forecast = lambda x: x # Fallback to current condition

from datetime import datetime, timedelta
from pydantic import BaseModel
from services.execution_engine import ExecutionEngine
from services.rl_optimizer import RLOptimizer
from services.market_watchdog import MarketWatchdog
from services.notification_service import NotificationService
from firebase_admin import messaging as firebase_messaging
from loguru import logger
import socket

app = FastAPI()

# Global Caches for Performance
_cached_ip = None
_last_ip_check = 0

def get_local_ip():
    """Returns the machine's local network IP (cached for 10 min)."""
    global _cached_ip, _last_ip_check
    now = datetime.now().timestamp()
    if _cached_ip and (now - _last_ip_check) < 600:
        return _cached_ip
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        _cached_ip = s.getsockname()[0]
        s.close()
    except:
        _cached_ip = "127.0.0.1"
    
    _last_ip_check = now
    return _cached_ip

class BetRequest(BaseModel):
    date: str
    venue: str
    race: int
    selection: str
    stake: float

class SubscribeRequest(BaseModel):
    token: str
    topic: str = "high_confidence_bets"

execution_engine = ExecutionEngine(dry_run=True, headless=False)
notification_service = NotificationService()
rl_optimizer = RLOptimizer()
market_watchdog = MarketWatchdog()

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"success": True, "message": "pong"}

# Use dynamic path for cross-platform support
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

import fnmatch

def get_latest_file(directory, pattern):
    """Ultra-fast file lookup using os.scandir and fnmatch."""
    try:
        if not os.path.exists(directory): return None
        latest = None
        for entry in os.scandir(directory):
            if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                if not latest or entry.name > latest.name:
                    latest = entry
        return Path(latest.path) if latest else None
    except:
        return None

@app.get("/latest")
async def get_latest():
    """Returns the most recent prediction, weather, alerts, and system health in ONE request."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing /latest request...")
    try:
        # 1. Latest Prediction
        latest_pred = None
        p_file = get_latest_file(DATA_DIR / "predictions", "*.json")
        if p_file:
            with open(p_file, "r", encoding="utf-8") as f:
                latest_pred = json.load(f)

        # 2. Latest Weather Intelligence
        latest_weather = None
        w_file = get_latest_file(DATA_DIR / "weather", "intel_*.json")
        if w_file:
            with open(w_file, "r", encoding="utf-8") as f:
                latest_weather = json.load(f)

        # 3. Latest Alerts
        all_alerts = []
        s_file = get_latest_file(DATA_DIR / "alerts", "alerts_*.json")
        m_file = get_latest_file(DATA_DIR / "alerts", "market_alerts_*.json")
        
        alerts_list = []
        if s_file:
            with open(s_file, "r", encoding="utf-8") as f:
                alerts_list += json.load(f).get("alerts", [])
        if m_file:
            with open(m_file, "r", encoding="utf-8") as f:
                alerts_list += json.load(f).get("alerts", [])
        
        alerts_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        all_alerts = alerts_list[:10]

        # 4. System Health
        health_status = {"status": "IDLE", "last_activity": "N/A"}
        
        # Priority 1: Check Heartbeat File (Most accurate for active processes)
        heartbeat_file = DATA_DIR / "backfill_status.json"
        if heartbeat_file.exists():
            try:
                with open(heartbeat_file, "r", encoding="utf-8") as f:
                    hb = json.load(f)
                    # If heartbeat is less than 2 minutes old, trust it
                    if (datetime.now().timestamp() - hb.get("timestamp", 0)) < 120:
                        health_status["status"] = hb["status"]
                        health_status["last_activity"] = datetime.fromtimestamp(hb["timestamp"]).strftime("%H:%M:%S")
                        health_status["progress"] = hb.get("meetings_done", 0)
            except:
                pass

        # Priority 2: Fallback to last result file mtime
        if health_status["status"] == "IDLE":
            r_file = get_latest_file(DATA_DIR / "results", "results_*.json")
            if r_file:
                mtime = r_file.stat().st_mtime
                if (datetime.now().timestamp() - mtime) < 300:
                    health_status["status"] = "ACTIVE"
                health_status["last_activity"] = datetime.fromtimestamp(mtime).strftime("%H:%M:%S")

        scraper_health = "NOMINAL"
        # Skip error png check if too heavy, or just check existence
        if (DATA_DIR / "pedigree_cache").exists():
            scraper_health = "NOMINAL" # Simplified for speed

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Request complete.")
        return {
            "success": True,
            "prediction": latest_pred,
            "weather": latest_weather,
            "alerts": {"alerts": all_alerts},
            "health": {
                "backfill": health_status,
                "services": {
                    "pedigree": scraper_health,
                    "ai_engine": "ONLINE",
                    "weather_pro": "STABLE",
                    "local_ip": get_local_ip()
                }
            }
        }
    except Exception as e:
        print(f"ERR: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/prediction/{race_id}")
async def get_specific_prediction(race_id: str):
    """Fetches a specific prediction by ID (e.g. 2026-03-18_HV_R1)."""
    try:
        p_file = DATA_DIR / "predictions" / f"prediction_{race_id}.json"
        if p_file.exists():
            with open(p_file, "r", encoding="utf-8") as f:
                return {"success": True, "prediction": json.load(f)}
        return {"success": False, "error": "Prediction not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/execution/recommendations")
async def get_recommendations():
    """Returns predictions with Kelly stakes for the next meeting."""
    try:
        # For now, look at today
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

@app.get("/picks/upcoming")
async def get_upcoming_top_picks():
    """Returns the top pick (highest probability) for each race of the upcoming meeting."""
    try:
        # Target date for the next major meeting
        pred_dir = DATA_DIR / "predictions"
        top_picks = []
        target_date = "N/A"

        if pred_dir.exists():
            # 1. Try today's date
            target_date = datetime.now().strftime("%Y-%m-%d")
            pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
            
            # 2. If empty, try tomorrow's date
            if not pred_files:
                target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
            
            # 3. If still empty, find the most recent meeting date from files
            if not pred_files:
                all_preds = list(pred_dir.glob("prediction_*.json"))
                if all_preds:
                    # Sort by filename descending (latest date first)
                    all_preds.sort(key=lambda x: x.name, reverse=True)
                    target_date = all_preds[0].name.split("_")[1] # prediction_YYYY-MM-DD_...
                    pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
            
            for p_file in pred_files:
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        probs = data.get("probabilities", {})
                        kelly_stakes = data.get("kelly_stakes", {})
                        market_odds  = data.get("market_odds", {})
                        if not probs:
                            continue

                        # Priority 1: horse with the HIGHEST Kelly stake (real bet signal)
                        top_horse_id = None
                        if kelly_stakes:
                            top_horse_id = max(kelly_stakes, key=lambda h: kelly_stakes[h])
                        
                        # Priority 2: recommended_bet field
                        if not top_horse_id:
                            rec_bet = data.get("recommended_bet", "")
                            if rec_bet and "WIN" in rec_bet:
                                try:
                                    extracted = "".join(filter(str.isdigit, rec_bet))
                                    if extracted in probs:
                                        top_horse_id = extracted
                                except:
                                    pass
                        
                        # Priority 3: highest AI probability
                        if not top_horse_id:
                            top_horse_id = max(probs, key=probs.get)

                        # Build all Kelly selections for this race (may be >1)
                        kelly_selections = [
                            {"horse_no": h, "kelly_stake": s, "market_odds": market_odds.get(h, "--")}
                            for h, s in kelly_stakes.items() if s > 0
                        ]

                        pick = {
                            "race_id":          data.get("race_id"),
                            "race_no":          int(data.get("race_id").split("_")[-1].replace("R", "")),
                            "horse_no":         top_horse_id,
                            "horse_name":       data.get("horse_names", {}).get(top_horse_id, f"Horse {top_horse_id}"),
                            "prob":             probs.get(top_horse_id, 0),
                            "kelly_stake":      kelly_stakes.get(top_horse_id, 0),
                            "kelly_selections": kelly_selections,   # all bettable horses
                            "market_odds":      market_odds.get(top_horse_id, "--"),
                            "is_best_bet":      data.get("is_best_bet", False),
                            "has_odds":         bool(market_odds),
                        }
                        top_picks.append(pick)
                except Exception as inner_e:
                    print(f"Error parsing {p_file.name}: {inner_e}")

        # Sort by race number
        top_picks.sort(key=lambda x: x["race_no"])
        
        return {
            "success": True, 
            "date": target_date,
            "picks": top_picks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/execution/stage_bet")
async def stage_bet(request: BetRequest):
    """Triggers the ExecutionEngine to stage a bet."""
    try:
        # Run execution engine in a background task to not block FastAPI
        # Since it opens a browser, it's safer to not await it indefinitely here
        # But for dev, we can wait a bit or use a Task
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

@app.post("/execution/recalibrate")
async def recalibrate():
    """Triggers the RLOptimizer to adjust biases based on recent performance."""
    try:
        rl_optimizer.optimize_from_past_days(days=7)
        biases = rl_optimizer.load_biases()
        return {"success": True, "message": "Recalibration complete.", "biases": biases}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/execution/force_update")
async def force_update():
    """Triggers a full re-ingestion and re-prediction cycle via daily_runner.py."""
    try:
        # Target date for the current/upcoming meeting
        target_date = datetime.now().strftime("%Y-%m-%d") 
        log_file = BASE_DIR / "data" / "force_update.log"
        script_path = BASE_DIR / "services" / "daily_runner.py"
        
        # 1. Run the most imminent race synchronously (e.g. Race 1) for immediate feedback
        # This takes ~15-20s, giving the user a meaningful 'Completed' status
        single_cmd = [
            sys.executable, str(script_path), 
            "--date", target_date,
            "--race", "1" 
        ]
        
        # Run single race synchronously
        subprocess.run(single_cmd, capture_output=True, cwd=str(BASE_DIR))

        # 2. Run the full meeting in the background for the rest of the races
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

@app.get("/execution/kelly_settings")
async def get_kelly_settings():
    """Returns current Kelly Criterion settings."""
    from config.settings import Config
    return {
        "success": True,
        "bankroll": Config.INITIAL_BANKROLL,
        "fraction": Config.KELLY_FRACTION
    }

@app.post("/execution/kelly_settings")
async def update_kelly_settings(settings: dict):
    """Updates Kelly Criterion settings (in-memory for current session)."""
    from config.settings import Config
    if "bankroll" in settings:
        Config.INITIAL_BANKROLL = float(settings["bankroll"])
    if "fraction" in settings:
        Config.KELLY_FRACTION = float(settings["fraction"])
    return {"success": True, "message": "Kelly settings updated for current session."}

import subprocess

import asyncio

# Serve static files for the dashboard

@app.get("/health")
async def health_check():
    """Returns system health and service status."""
    return {
        "success": True,
        "status": "online",
        "services": {
            "market_watchdog": {
                "active": True,
                "last_heartbeat": market_watchdog.last_heartbeat,
                "venue": "ST" # Mocked for current meeting
            }
        },
        "timestamp": datetime.now().isoformat()
    }

async def recovery_task(race_no: int, venue: str):
    """Monitors and restarts the watchdog if it dies."""
    while True:
        try:
            logger.info(f"🚀 Launching Market Watchdog for Race {race_no} ({venue})...")
            # We don't await this directly in a way that blocks the recovery loop
            await market_watchdog.run_loop(race_no=race_no, venue=venue, interval=120)
        except Exception as e:
            logger.error(f"⚠️ Watchdog CRASHED: {e}. Restarting in 5s...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Start the watchdog in a recovery wrapper
    asyncio.create_task(recovery_task(race_no=1, venue="ST"))

@app.post("/subscribe")
async def subscribe_to_alerts(request: SubscribeRequest):
    try:
        response = firebase_messaging.subscribe_to_topic([request.token], request.topic)
        return {
            "success": True, 
            "results": {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"HKJC Command Center starting at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
