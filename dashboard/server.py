import os
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

# Import extracted global state
from dependencies import (
    Config, get_current_meeting_info, market_watchdog, HK_TZ
)
from services.meeting_settlement import MeetingSettlement

# Routers
from routers import data, execution, debug, notifications

# WeatherNext 2 Integration (Safe Import)
try:
    wn_path = os.getenv("WEATHERNEXT_PATH")
    if not wn_path:
        sibling_wn = BASE_DIR.parent / "weathernext_pro/src"
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
    get_track_forecast = lambda x: x

app = FastAPI()

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(data.router)
app.include_router(execution.router)
app.include_router(debug.router)
app.include_router(notifications.router)

async def recovery_task(race_no: int, venue: str):
    """Monitors and restarts the watchdog if it dies."""
    while True:
        try:
            logger.info(f"🚀 Launching Market Watchdog for Race {race_no} ({venue})...")
            await market_watchdog.run_loop(race_no=race_no, venue=venue, interval=120)
        except Exception as e:
            logger.error(f"⚠️ Watchdog CRASHED: {e}. Restarting in 5s...")
            await asyncio.sleep(5)

async def auto_settlement_task(meeting_date: str, venue: str):
    """Waits until after the last race, then auto-settles the meeting."""
    settle_hour = 19 if venue == "ST" else 23
    now_hk = datetime.now(HK_TZ)
    start_time = now_hk.replace(hour=settle_hour, minute=0, second=0, microsecond=0)
    
    if now_hk < start_time:
        wait_secs = (start_time - now_hk).total_seconds()
        logger.info(f"🏁 Auto-settlement scheduled for {start_time.strftime('%H:%M')} HKT ({wait_secs/60:.0f} min from now)")
        await asyncio.sleep(wait_secs)
    
    report_file = Path("data/reports") / f"report_{meeting_date}_{venue}.md"
    if report_file.exists():
        logger.info(f"🏁 Settlement already done for {meeting_date} ({venue}). Skipping.")
        return
    
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
        
        await asyncio.sleep(900)
    
    logger.error(f"❌ Auto-settlement FAILED after 8 attempts for {meeting_date} ({venue})")

@app.on_event("startup")
async def startup_event():
    meeting_date, venue = get_current_meeting_info()
    if os.getenv("ENABLE_WATCHDOG", "true").lower() != "false":
        max_races = 11 if venue == "ST" else 9
        logger.info(f"📍 Initializing Watchdog for meeting: {meeting_date} ({venue}) — {max_races} races")
        for r in range(1, max_races + 1):
            asyncio.create_task(recovery_task(race_no=r, venue=venue))
            await asyncio.sleep(2)
        
        asyncio.create_task(auto_settlement_task(meeting_date, venue))
    else:
        logger.info(f"📍 Watchdog DISABLED (ENABLE_WATCHDOG=false). Dashboard reads from Firestore only.")

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
