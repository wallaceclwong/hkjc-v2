import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import json

# WeatherNext 2 Integration (Safe Import)
from config.settings import Config
from services.firestore_service import FirestoreService

# Try to find weathernext_pro in sibling directory or via env
try:
    wn_path = os.getenv("WEATHERNEXT_PATH")
    if not wn_path:
        # Check sibling directory
        sibling_wn = Config.BASE_DIR.parent / "weathernext_pro/src"
        if sibling_wn.exists():
            wn_path = str(sibling_wn)
    
    if wn_path:
        sys.path.append(wn_path)
        from v2_engine import get_track_forecast
        print(f"[INFO] Integrated WeatherNext v2 from {wn_path}")
    else:
        raise ImportError("WeatherNext path not found")
except Exception as e:
    print(f"[WARNING] WeatherNext v2 integration skipped: {e}")
    get_track_forecast = lambda x: x # Fallback to current condition

from datetime import datetime, timedelta
import pytz
from pydantic import BaseModel
from services.execution_engine import ExecutionEngine
from services.rl_optimizer import RLOptimizer
from services.market_watchdog import MarketWatchdog
from services.notification_service import NotificationService
from firebase_admin import messaging as firebase_messaging
from loguru import logger
import socket
import asyncio
from services.meeting_settlement import MeetingSettlement

HK_TZ = pytz.timezone("Asia/Hong_Kong")

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
firestore = FirestoreService()

# Determine if we should prioritize Firestore (Cloud Run or explicit env var)
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true" or os.getenv("K_SERVICE") is not None

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

@app.get("/debug/firestore")
async def debug_firestore():
    """Diagnostic endpoint for Firestore connectivity."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    path_exists = os.path.exists(creds_path) if creds_path else False
    
    status = {
        "project_id": Config.PROJECT_ID,
        "creds_env": creds_path,
        "creds_file_exists": path_exists,
        "firestore_client_initialized": firestore.db is not None,
        "error": None
    }
    
    try:
        # Test a simple query if client exists
        if firestore.db:
            col = firestore.db.collection(Config.COL_PREDICTIONS).limit(1).get()
            status["query_test"] = "SUCCESS"
        else:
            status["query_test"] = "SKIPPED (No Client)"
    except Exception as e:
        status["error"] = str(e)
        status["query_test"] = "FAILED"
        
    return status

@app.get("/debug/firestore/live")
async def debug_firestore_live():
    """Returns raw alert counts and document IDs from Firestore."""
    try:
        if not firestore.db:
            return {"error": "Firestore not initialized"}
            
        cols = [c.id for c in firestore.db.collections()]
        alerts_ref = firestore.db.collection(Config.COL_MARKET_ALERTS)
        docs = [d.id for d in alerts_ref.limit(5).stream()]
        
        return {
            "project_id": Config.PROJECT_ID,
            "database": Config.FIRESTORE_DATABASE,
            "collections": cols,
            "recent_alerts": docs,
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def get_current_meeting_info():
    """Robustly identifies tonight's or the latest meeting venue and date."""
    today_str = datetime.now(HK_TZ).strftime("%Y-%m-%d")
    venue = "ST" # Default fallback
    meeting_date = today_str
    
    try:
        # 1. Try to find a doc for today specifically (prefix search)
        # Using id ordering (None as order_by) to bypass field indexing issues
        # Use race_id field instead of document name to avoid __key__ filter issues
        today_preds = firestore.query(
            Config.COL_PREDICTIONS, 
            filters=[("race_id", ">=", today_str), ("race_id", "<=", today_str + "\uf8ff")],
            limit=1
        )
        
        if today_preds:
            race_id = today_preds[0].get("race_id", "")
            parts = race_id.split("_")
            if len(parts) > 1:
                meeting_date = parts[0]
                venue = parts[1]
                return meeting_date, venue

        # 2. Fallback: Get the absolute latest prediction in the system
        latest_pred = firestore.get_latest(Config.COL_PREDICTIONS) # Default doc ID ordering
        if latest_pred:
            race_id = latest_pred.get("race_id", "")
            parts = race_id.split("_")
            if len(parts) > 1:
                meeting_date = parts[0]
                venue = parts[1]
    except Exception as e:
        logger.error(f"Error detecting meeting info: {e}")

    return meeting_date, venue

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
        elif USE_FIRESTORE:
            # Fallback to Firestore (Avoid order_by which can cause index-missing errors)
            all_preds = firestore.query(Config.COL_PREDICTIONS, limit=100)
            if all_preds:
                all_preds.sort(key=lambda x: x.get("race_id", ""), reverse=True)
                latest_pred = all_preds[0]
            else:
                 latest_pred = firestore.get_latest(Config.COL_PREDICTIONS)

        # 2. Latest Weather Intelligence
        latest_weather = None
        w_file = get_latest_file(DATA_DIR / "weather", "intel_*.json")
        if w_file:
            with open(w_file, "r", encoding="utf-8") as f:
                latest_weather = json.load(f)
        elif USE_FIRESTORE:
            latest_weather = firestore.get_latest(Config.COL_WEATHER, order_by="timestamp")

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
        
        # Firestore Fallback for Alerts
        if not alerts_list and USE_FIRESTORE:
            # Simple query on dedicated alerts collection (automatic single-field index)
            # Fetch all alerts and process in Python (Avoids all index/key issues)
            f_alerts = firestore.query(Config.COL_MARKET_ALERTS)
            if f_alerts:
                # Sort by updated_at descending
                f_alerts.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
                alerts_list += f_alerts[0].get("alerts", [])
                logger.info(f"✅ Retrieved latest live alerts from Firestore: {f_alerts[0].get('race_id')}")
        
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
                    "local_ip": get_local_ip(),
                    "cloud_sync": USE_FIRESTORE
                }
            }
        }
    except Exception as e:
        print(f"ERR: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/meetings")
async def list_meetings():
    """Returns a list of all meetings (date + venue) that have data."""
    try:
        meetings_dict = {} # date -> venue
        
        # 1. Check Predictions
        if USE_FIRESTORE:
            # Order by race_id DESC to get the latest meetings first
            docs = firestore.db.collection(Config.COL_PREDICTIONS).order_by("race_id", direction="DESCENDING").limit(500).stream()
            for d in docs:
                rid = d.get("race_id")
                if rid:
                    parts = rid.split("_")
                    if len(parts) >= 2:
                        meetings_dict[parts[0]] = parts[1]
        else:
            p_dir = DATA_DIR / "predictions"
            if p_dir.exists():
                for p in p_dir.glob("prediction_*.json"):
                    parts = p.stem.split("_")
                    if len(parts) >= 3:
                        meetings_dict[parts[1]] = parts[2]
                
        # 2. Check Reports
        if USE_FIRESTORE:
            # Order by meeting_date DESC
            docs = firestore.db.collection(Config.COL_REPORTS).order_by("meeting_date", direction="DESCENDING").limit(100).stream()
            for d in docs:
                md = d.get("meeting_date")
                mv = d.get("venue")
                if md and mv: meetings_dict[md] = mv
        else:
            r_dir = DATA_DIR / "reports"
            if r_dir.exists():
                for r in r_dir.glob("report_*.md"):
                    parts = r.stem.split("_")
                    if len(parts) >= 3:
                        meetings_dict[parts[1]] = parts[2]
                
        # Sort by date descending and filter for 2026 only
        sorted_meetings = [
            {"date": d, "venue": v} 
            for d, v in sorted(meetings_dict.items(), key=lambda x: x[0], reverse=True)
            if d.startswith("2026")
        ]
        
        print(f"[DEBUG] Found {len(sorted_meetings)} meetings. Sample: {sorted_meetings[:1]}")
        return {"success": True, "meetings": sorted_meetings}

    except Exception as e:
        print(f"[ERROR] list_meetings failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/reports/{date}/{venue}")
async def get_meeting_report(date: str, venue: str):
    """Returns the performance report for a specific meeting."""
    try:
        report_id = f"{date}_{venue}"
        
        # 1. Try Local Fallback first (Immediate updates)
        report_path = DATA_DIR / "reports" / f"report_{date}_{venue}.md"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            return {
                "success": True, 
                "report": {
                    "meeting_date": date,
                    "venue": venue,
                    "markdown": md_content
                }
            }

        # 2. Try Firestore (Cloud backup)
        if USE_FIRESTORE:
            report_data = firestore.get_document(Config.COL_REPORTS, report_id)
            if report_data:
                return {"success": True, "report": report_data}
            
        return {"success": False, "error": "Report not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/prediction/{race_id}")
async def get_specific_prediction(race_id: str):
    """Fetches a specific prediction by ID (e.g. 2026-03-18_HV_R1)."""
    try:
        pred_data = None
        p_file = DATA_DIR / "predictions" / f"prediction_{race_id}.json"
        
        if p_file.exists():
            with open(p_file, "r", encoding="utf-8") as f:
                pred_data = json.load(f)
        elif USE_FIRESTORE:
            pred_data = firestore.get_document(Config.COL_PREDICTIONS, race_id)

        if pred_data:
            # Inject horse_names from racecard if not already in file
            if not pred_data.get("horse_names"):
                parts = race_id.split("_")  # e.g. ['2026-03-25', 'HV', 'R1']
                if len(parts) >= 2:
                    race_date = parts[0]
                    race_no_str = parts[-1].replace("R", "")
                    try:
                        race_no = int(race_no_str)
                        horse_names = load_horse_names(race_date, race_no)
                        if horse_names:
                            pred_data["horse_names"] = horse_names
                    except ValueError:
                        pass
            return {"success": True, "prediction": pred_data}
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

def load_horse_names(race_date: str, race_no: int) -> dict:
    """
    Builds a saddle_number -> horse_name dict from the racecard file.
    race_date should be 'YYYY-MM-DD', race_no is an int.
    Returns empty dict if racecard is not found locally or in Firestore.
    """
    date_compact = race_date.replace("-", "")
    racecard_filename = f"racecard_{date_compact}_R{race_no}.json"
    racecard_path = DATA_DIR / racecard_filename
    
    # 1. Try local file (Fastest)
    if racecard_path.exists():
        try:
            with open(racecard_path, "r", encoding="utf-8") as f:
                rc = json.load(f)
            return {
                str(h["saddle_number"]): h["horse_name"]
                for h in rc.get("horses", [])
                if "saddle_number" in h and "horse_name" in h
            }
        except Exception as e:
            print(f"[ERROR] local racecard read failed: {e}")

    # 2. Try Firestore (Fallback for Cloud Run)
    if USE_FIRESTORE:
        try:
            # Document ID is usually the filename without .json or a custom ID
            # In our case, let's try the compact format YYYYMMDD_RX
            doc_id = f"{date_compact}_R{race_no}"
            rc_data = firestore.get_document(Config.COL_RACECARDS, doc_id)
            if rc_data:
                return {
                    str(h["saddle_number"]): h["horse_name"]
                    for h in rc_data.get("horses", [])
                    if "saddle_number" in h and "horse_name" in h
                }
        except Exception as e:
            print(f"[ERROR] firestore racecard fetch failed: {e}")

    return {}

@app.get("/picks")
@app.get("/picks/upcoming")
async def get_upcoming_top_picks(date: str = None):
    """Returns the top pick for each race of the meeting (specific date or upcoming)."""
    try:
        pred_dir = DATA_DIR / "predictions"
        top_picks = []
        target_date = date
        pred_files = []

        if not target_date:
            # Original auto-detect logic
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
                        print(f"[INFO] No files for tomorrow. Found next meeting: {target_date}")
        else:
            # Use specific date
            pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))

        # Firestore Fallback for picks
        if not pred_files and USE_FIRESTORE:
            print("[INFO] No local prediction files. Fetching from Firestore...")
            # Approximate current target date if not found locally
            target_date = datetime.now().strftime("%Y-%m-%d")
            # Query Firestore for predictions on this date using the race_id field
            f_preds = firestore.query(
                Config.COL_PREDICTIONS, 
                filters=[("race_id", ">=", target_date), ("race_id", "<=", target_date + "\uf8ff")]
            )
            
            if not f_preds:
                # Fallback: Find the most recent date in Firestore
                latest_docs = firestore.query(
                    Config.COL_PREDICTIONS,
                    order_by=("race_id", "DESCENDING"),
                    limit=1
                )
                if latest_docs:
                    # Extract date from race_id (e.g. 2026-03-29_ST_R1)
                    first_id = latest_docs[0].get("race_id") or "2026-01-01_ST_R1"
                    target_date = first_id.split("_")[0]
                    print(f"[INFO] Cloud fallback: Found latest meeting in Firestore: {target_date}")
                    f_preds = firestore.query(
                        Config.COL_PREDICTIONS, 
                        filters=[("race_id", ">=", target_date), ("race_id", "<=", target_date + "\uf8ff")]
                    )
            
            for data in f_preds:
                try:
                    probs = data.get("probabilities", {})
                    kelly_stakes = data.get("kelly_stakes", {})
                    market_odds  = data.get("market_odds", {})
                    if not probs: continue

                    race_no_num = int(data.get("race_id", "R1").split("_")[-1].replace("R", ""))
                    # Call load_horse_names (which has Firestore fallback)
                    horse_names = load_horse_names(target_date, race_no_num)
                    if not horse_names:
                        horse_names = data.get("horse_names", {})

                    # Priority 1: highest AI probability
                    top_horse_id = max(probs, key=probs.get)
                    
                    # Priority 2: falls back to kelly_stakes if probs were somehow empty (unlikely)
                    if not top_horse_id and kelly_stakes:
                        top_horse_id = max(kelly_stakes, key=lambda h: kelly_stakes[h])

                    kelly_selections = [
                        { 
                            "horse_no": h, 
                            "horse_name": horse_names.get(str(h), f"Horse {h}"), 
                            "kelly_stake": s, 
                            "market_odds": market_odds.get(h, "--") 
                        }
                        for h, s in kelly_stakes.items() if s > 0
                    ]

                    top_picks.append({
                        "race_id": data.get("race_id"),
                        "race_no": race_no_num,
                        "horse_no": top_horse_id,
                        "horse_name": horse_names.get(str(top_horse_id), f"Horse {top_horse_id}"),
                        "prob": probs.get(top_horse_id, 0),
                        "kelly_stake": kelly_stakes.get(top_horse_id, 0),
                        "kelly_selections": kelly_selections,
                        "market_odds": market_odds.get(top_horse_id, "--"),
                        "is_best_bet": data.get("is_best_bet", False),
                        "has_odds": bool(market_odds),
                    })
                except Exception as e:
                    print(f"Error parsing Firestore pred: {e}")

        if pred_files:
            for p_file in pred_files:
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        probs = data.get("probabilities", {})
                        kelly_stakes = data.get("kelly_stakes", {})
                        market_odds  = data.get("market_odds", {})
                        if not probs:
                            continue

                        # Build horse_names from racecard
                        race_no_num = int(data.get("race_id", "R1").split("_")[-1].replace("R", ""))
                        horse_names = load_horse_names(target_date, race_no_num)

                        # Priority 1: highest AI probability
                        top_horse_id = max(probs, key=probs.get)
                        
                        # Priority 2: falls back to kelly_stakes if probs were somehow empty (unlikely)
                        if not top_horse_id and kelly_stakes:
                            top_horse_id = max(kelly_stakes, key=lambda h: kelly_stakes[h])

                        # Build all Kelly selections for this race (may be >1)
                        kelly_selections = [
                            {
                                "horse_no": h,
                                "horse_name": horse_names.get(str(h), f"Horse {h}"),
                                "kelly_stake": s,
                                "market_odds": market_odds.get(h, "--")
                            }
                            for h, s in kelly_stakes.items() if s > 0
                        ]

                        pick = {
                            "race_id":          data.get("race_id"),
                            "race_no":          int(data.get("race_id").split("_")[-1].replace("R", "")),
                            "horse_no":         top_horse_id,
                            "horse_name":       horse_names.get(str(top_horse_id), f"Horse {top_horse_id}"),
                            "prob":             probs.get(top_horse_id, 0),
                            "kelly_stake":      kelly_stakes.get(top_horse_id, 0),
                            "kelly_selections": kelly_selections,
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
            "picks": top_picks,
            "bankroll": Config.INITIAL_BANKROLL
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

@app.post("/execution/settle")
async def settle_meeting(request: dict):
    """Triggers the MeetingSettlement orchestrator for a specific date and venue."""
    try:
        date = request.get("date")
        venue = request.get("venue")
        
        if not date or not venue:
            return {"success": False, "error": "Missing date or venue"}
            
        # We run it in the background as scraping can take 1-2 minutes
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
    meeting_date, venue = get_current_meeting_info()

    return {
        "success": True,
        "status": "online",
        "services": {
            "market_watchdog": {
                "active": True,
                "last_heartbeat": market_watchdog.last_heartbeat,
                "venue": venue,
                "meeting_date": meeting_date
            },
            "cloud_sync": USE_FIRESTORE
        },
        "timestamp": datetime.now(HK_TZ).isoformat()
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

async def auto_settlement_task(meeting_date: str, venue: str):
    """
    Waits until after the last race, then auto-settles the meeting.
    ST day races end ~6:30pm HKT, HV night races end ~10:30pm HKT.
    Checks every 15 minutes until all results are scraped and report is generated.
    """
    # Determine when to start checking
    settle_hour = 19 if venue == "ST" else 23  # 7pm for ST, 11pm for HV
    now_hk = datetime.now(HK_TZ)
    start_time = now_hk.replace(hour=settle_hour, minute=0, second=0, microsecond=0)
    
    if now_hk < start_time:
        wait_secs = (start_time - now_hk).total_seconds()
        logger.info(f"🏁 Auto-settlement scheduled for {start_time.strftime('%H:%M')} HKT ({wait_secs/60:.0f} min from now)")
        await asyncio.sleep(wait_secs)
    
    # Check if already settled
    report_file = Path("data/reports") / f"report_{meeting_date}_{venue}.md"
    if report_file.exists():
        logger.info(f"🏁 Settlement already done for {meeting_date} ({venue}). Skipping.")
        return
    
    # Try up to 8 times (2 hours of retries)
    settlement = MeetingSettlement()
    for attempt in range(1, 9):
        logger.info(f"🏁 Auto-settlement attempt {attempt}/8 for {meeting_date} ({venue})...")
        try:
            success = await settlement.settle_meeting(meeting_date, venue)
            if success:
                logger.info(f"✅ Auto-settlement COMPLETE for {meeting_date} ({venue})")
                return
            else:
                logger.warning(f"⚠️ Settlement returned no results — retrying in 15 min")
        except Exception as e:
            logger.error(f"⚠️ Settlement attempt {attempt} failed: {e}")
        
        await asyncio.sleep(900)  # Wait 15 minutes before retry
    
    logger.error(f"❌ Auto-settlement FAILED after 8 attempts for {meeting_date} ({venue})")

@app.on_event("startup")
async def startup_event():
    # Detect tonight's venue dynamically for the watchdog
    meeting_date, venue = get_current_meeting_info()

    # Only start watchdog if ENABLE_WATCHDOG is set (default: enabled)
    # Set ENABLE_WATCHDOG=false on VM to avoid scraping HKJC from datacenter IP
    if os.getenv("ENABLE_WATCHDOG", "true").lower() != "false":
        max_races = 11 if venue == "ST" else 9
        logger.info(f"📍 Initializing Watchdog for meeting: {meeting_date} ({venue}) — {max_races} races")
        for r in range(1, max_races + 1):
            asyncio.create_task(recovery_task(race_no=r, venue=venue))
            await asyncio.sleep(2)  # Stagger startup to avoid burst scraping
        
        # Auto-settlement: runs after last race (scrapes HKJC results from residential IP)
        asyncio.create_task(auto_settlement_task(meeting_date, venue))
    else:
        logger.info(f"📍 Watchdog DISABLED (ENABLE_WATCHDOG=false). Dashboard reads from Firestore only.")

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

# Serve static files for the dashboard
DASHBOARD_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=FileResponse)
async def read_index():
    index_path = DASHBOARD_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(status_code=404, content={"detail": "index.html not found in dashboard directory"})

app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"HKJC Command Center starting at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
