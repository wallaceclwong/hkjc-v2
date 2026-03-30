import os
from datetime import datetime
from fastapi import APIRouter
from loguru import logger

from dashboard.dependencies import (
    firestore, Config, get_current_meeting_info, USE_FIRESTORE,
    market_watchdog, HK_TZ
)

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"success": True, "message": "pong"}

@router.get("/health")
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

@router.get("/debug/firestore")
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
        if firestore.db:
            col = firestore.db.collection(Config.COL_PREDICTIONS).limit(1).get()
            status["query_test"] = "SUCCESS"
        else:
            status["query_test"] = "SKIPPED (No Client)"
    except Exception as e:
        status["error"] = str(e)
        status["query_test"] = "FAILED"
        
    return status

@router.get("/debug/firestore/live")
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
