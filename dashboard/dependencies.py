import os
import sys
from pathlib import Path
import socket
import fnmatch
import json
from datetime import datetime
import pytz
from loguru import logger

# Try to pull in config without breaking if not run from root
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import Config
# Lazy Loading Container
class AppState:
    def __init__(self):
        self._execution_engine = None
        self._notification_service = None
        self._rl_optimizer = None
        self._market_watchdog = None
        self._firestore = None

    @property
    def execution_engine(self):
        if self._execution_engine is None:
            from services.execution_engine import ExecutionEngine
            self._execution_engine = ExecutionEngine(dry_run=True, headless=False)
        return self._execution_engine

    @property
    def notification_service(self):
        if self._notification_service is None:
            from services.notification_service import NotificationService
            self._notification_service = NotificationService()
        return self._notification_service

    @property
    def rl_optimizer(self):
        if self._rl_optimizer is None:
            from services.rl_optimizer import RLOptimizer
            self._rl_optimizer = RLOptimizer()
        return self._rl_optimizer

    @property
    def market_watchdog(self):
        if self._market_watchdog is None:
            from services.market_watchdog import MarketWatchdog
            self._market_watchdog = MarketWatchdog()
        return self._market_watchdog

    @property
    def firestore(self):
        if self._firestore is None:
            from services.firestore_service import FirestoreService
            self._firestore = FirestoreService()
        return self._firestore

state = AppState()

# For backward compatibility with existing imports in other files
def get_execution_engine(): return state.execution_engine
def get_market_watchdog(): return state.market_watchdog
def get_firestore(): return state.firestore

# Dynamic Proxy to handle true lazy loading without breaking existing 'from dependencies import x'
class DependencyProxy:
    def __init__(self, name):
        self._name = name

    def _get_target(self):
        return getattr(state, self._name)

    def __getattr__(self, name):
        return getattr(self._get_target(), name)
    
    def __getitem__(self, key):
        return self._get_target()[key]

    def __call__(self, *args, **kwargs):
        return self._get_target()(*args, **kwargs)

    def __repr__(self):
        return repr(self._get_target())

    def __str__(self):
        return str(self._get_target())

# Overwrite the global variables with TRUE proxies
execution_engine = DependencyProxy("execution_engine")
notification_service = DependencyProxy("notification_service")
rl_optimizer = DependencyProxy("rl_optimizer")
market_watchdog = DependencyProxy("market_watchdog")
firestore = DependencyProxy("firestore")

# Environment / Paths
DATA_DIR = BASE_DIR / "data"
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true" or os.getenv("K_SERVICE") is not None
HK_TZ = pytz.timezone("Asia/Hong_Kong")

# Caches
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

def get_current_meeting_info():
    """Robustly identifies tonight's or the latest meeting venue and date."""
    today_str = datetime.now(HK_TZ).strftime("%Y-%m-%d")
    venue = "ST" # Default fallback
    meeting_date = today_str
    
    try:
        # 1. Try to find a doc for today specifically (prefix search)
        today_preds = firestore.query(
            Config.COL_PREDICTIONS, 
            filters=[("race_id", ">=", today_str), ("race_id", "<=", today_str + "\uf8ff")],
            limit=1
        )
        if today_preds:
            race_id = today_preds[0].get("race_id", "")
            parts = race_id.split("_")
            if len(parts) > 1:
                return parts[0], parts[1]

        # 2. Fallback: Get absolute latest
        latest_pred = firestore.get_latest(Config.COL_PREDICTIONS)
        if latest_pred:
            race_id = latest_pred.get("race_id", "")
            parts = race_id.split("_")
            if len(parts) > 1:
                return parts[0], parts[1]
    except Exception as e:
        logger.error(f"Error detecting meeting info: {e}")

    return meeting_date, venue

def load_horse_names(race_date: str, race_no: int) -> dict:
    """
    Builds a saddle_number -> horse_name dict from the racecard file.
    race_date should be 'YYYY-MM-DD', race_no is an int.
    Returns empty dict if racecard is not found locally or in Firestore.
    """
    date_compact = race_date.replace("-", "")
    racecard_filename = f"racecard_{date_compact}_R{race_no}.json"
    racecard_path = DATA_DIR / racecard_filename
    
    if racecard_path.exists():
        try:
            with open(racecard_path, "r", encoding="utf-8") as f:
                rc = json.load(f)
            return {str(h["saddle_number"]): h["horse_name"] for h in rc.get("horses", []) if "saddle_number" in h and "horse_name" in h}
        except Exception as e:
            logger.error(f"local racecard read failed: {e}")

    if USE_FIRESTORE:
        try:
            doc_id = f"{date_compact}_R{race_no}"
            rc_data = firestore.get_document(Config.COL_RACECARDS, doc_id)
            if rc_data:
                return {str(h["saddle_number"]): h["horse_name"] for h in rc_data.get("horses", []) if "saddle_number" in h and "horse_name" in h}
        except Exception as e:
            logger.error(f"firestore racecard fetch failed: {e}")

    return {}
