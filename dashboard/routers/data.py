from fastapi import APIRouter
from datetime import datetime, timedelta
import json
from loguru import logger

from loguru import logger

from dashboard.dependencies import (
    DATA_DIR, USE_FIRESTORE, firestore, get_latest_file, 
    get_local_ip, load_horse_names, Config
)
from services.bankroll_manager import BankrollManager

# Lazy-loaded bankroll manager to prevent blocking on import
_bankroll_manager = None
def get_bankroll_manager():
    global _bankroll_manager
    if _bankroll_manager is None:
        _bankroll_manager = BankrollManager()
    return _bankroll_manager

router = APIRouter()

@router.get("/latest")
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

        # 3. Latest Alerts (REMOVED)
        all_alerts = []

        # 4. System Health
        health_status = {"status": "IDLE", "last_activity": "N/A"}
        
        heartbeat_file = DATA_DIR / "backfill_status.json"
        if heartbeat_file.exists():
            try:
                with open(heartbeat_file, "r", encoding="utf-8") as f:
                    hb = json.load(f)
                    if (datetime.now().timestamp() - hb.get("timestamp", 0)) < 120:
                        health_status["status"] = hb["status"]
                        health_status["last_activity"] = datetime.fromtimestamp(hb["timestamp"]).strftime("%H:%M:%S")
                        health_status["progress"] = hb.get("meetings_done", 0)
            except:
                pass

        if health_status["status"] == "IDLE":
            r_file = get_latest_file(DATA_DIR / "results", "results_*.json")
            if r_file:
                mtime = r_file.stat().st_mtime
                if (datetime.now().timestamp() - mtime) < 300:
                    health_status["status"] = "ACTIVE"
                health_status["last_activity"] = datetime.fromtimestamp(mtime).strftime("%H:%M:%S")

        scraper_health = "NOMINAL"
        if (DATA_DIR / "pedigree_cache").exists():
            scraper_health = "NOMINAL"

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

@router.get("/meetings")
async def list_meetings():
    """Returns a list of all meetings (date + venue) that have data."""
    try:
        meetings_dict = {}
        
        if USE_FIRESTORE:
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
                
        if USE_FIRESTORE:
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
                
        # Also check for meetings with racecards (even if no predictions yet)
        rc_dir = DATA_DIR
        for rc in rc_dir.glob("racecard_*.json"):
            parts = rc.stem.split("_")
            if len(parts) >= 3:
                # racecard_YYYYMMDD_RX.json -> date = YYYY-MM-DD
                date_compact = parts[1]
                if len(date_compact) == 8:
                    date_str = f"{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:]}"
                    # Try to determine venue from racecard content
                    venue = "ST"  # Default
                    try:
                        with open(rc, "r", encoding="utf-8") as f:
                            rc_data = json.load(f)
                            if isinstance(rc_data, dict) and "venue" in rc_data:
                                venue = rc_data["venue"]
                    except:
                        pass
                    meetings_dict[date_str] = venue
        
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

@router.get("/reports/{date}/{venue}")
async def get_meeting_report(date: str, venue: str):
    """Returns the performance report for a specific meeting."""
    try:
        report_id = f"{date}_{venue}"
        
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

        if USE_FIRESTORE:
            report_data = firestore.get_document(Config.COL_REPORTS, report_id)
            if report_data:
                return {"success": True, "report": report_data}
            
        return {"success": False, "error": "Report not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/prediction/{race_id}")
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
            if not pred_data.get("horse_names"):
                parts = race_id.split("_")
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

@router.get("/picks")
@router.get("/picks/upcoming")
async def get_upcoming_top_picks(date: str = None, venue: str = None):
    """Returns the top pick for each race of the meeting (specific date or upcoming)."""
    try:
        pred_dir = DATA_DIR / "predictions"
        top_picks = []
        target_date = date
        pred_files = []

        if not target_date:
            if pred_dir.exists():
                target_date = datetime.now().strftime("%Y-%m-%d")
                pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
                
                if not pred_files:
                    target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
                
                if not pred_files:
                    import re
                    valid_date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
                    all_preds = [p for p in pred_dir.glob("prediction_*.json") if valid_date_pattern.match(p.name.split("_")[1])]
                    if all_preds:
                        all_preds.sort(key=lambda x: x.name, reverse=True)
                        target_date = all_preds[0].name.split("_")[1]
                        pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))
                        print(f"[INFO] Found next meeting: {target_date}")
        else:
            pred_files = list(pred_dir.glob(f"prediction_{target_date}_*.json"))

        if not pred_files and USE_FIRESTORE:
            print("[INFO] No local prediction files. Fetching from Firestore...")
            target_date = datetime.now().strftime("%Y-%m-%d")
            f_preds = firestore.query(
                Config.COL_PREDICTIONS, 
                filters=[("race_id", ">=", target_date), ("race_id", "<=", target_date + "\uf8ff")]
            )
            
            if not f_preds:
                latest_docs = firestore.query(
                    Config.COL_PREDICTIONS,
                    order_by=("race_id", "DESCENDING"),
                    limit=1
                )
                if latest_docs:
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
                    horse_names = load_horse_names(target_date, race_no_num)
                    if not horse_names:
                        horse_names = data.get("horse_names", {})

                    top_horse_id = max(probs, key=probs.get)
                    if not top_horse_id and kelly_stakes:
                        top_horse_id = max(kelly_stakes, key=lambda h: kelly_stakes[h])

                    kelly_selections = [
                        { "horse_no": h, "horse_name": horse_names.get(str(h), f"Horse {h}"), "kelly_stake": s, "market_odds": market_odds.get(h, "--") }
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

                        race_no_num = int(data.get("race_id", "R1").split("_")[-1].replace("R", ""))
                        horse_names = load_horse_names(target_date, race_no_num)

                        top_horse_id = max(probs, key=probs.get)
                        if not top_horse_id and kelly_stakes:
                            top_horse_id = max(kelly_stakes, key=lambda h: kelly_stakes[h])

                        kelly_selections = [
                            { "horse_no": h, "horse_name": horse_names.get(str(h), f"Horse {h}"), "kelly_stake": s, "market_odds": market_odds.get(h, "--") }
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
                        # Avoid duplicates - skip if this race already added from Firestore
                        if not any(p["race_no"] == pick["race_no"] for p in top_picks):
                            top_picks.append(pick)
                except Exception as inner_e:
                    print(f"Error parsing {p_file.name}: {inner_e}")

        top_picks.sort(key=lambda x: x["race_no"])
        
        # Determine venue from first pick
        venue = ""
        if top_picks:
            venue = top_picks[0].get("race_id", "").split("_")[1] if len(top_picks[0].get("race_id", "").split("_")) > 1 else ""
        
        return {
            "success": True, 
            "date": target_date,
            "venue": venue,
            "picks": top_picks,
            "bankroll": get_bankroll_manager().get_current_bankroll()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
