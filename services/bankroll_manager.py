import os
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any

from config.settings import Config
from services.firestore_service import FirestoreService

class BankrollManager:
    def __init__(self):
        self.data_dir = Path(Config.BASE_DIR) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.data_dir / "bankroll.json"
        
        # Determine if we should use firestore to sync
        self.use_firestore = getattr(Config, "USE_FIRESTORE", True)
        self.firestore = FirestoreService() if self.use_firestore else None
        
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Creates the initial bankroll state if it doesn't exist."""
        if not self.filepath.exists():
            # Try to pull from Firestore first
            if self.use_firestore:
                fs_data = self.firestore.get_document(Config.COL_BANKROLL, "current_state")
                if fs_data:
                    self._save_local(fs_data)
                    return
            
            # Seed with INITIAL_BANKROLL
            initial_state = {
                "current_bankroll": Config.INITIAL_BANKROLL,
                "high_water_mark": Config.INITIAL_BANKROLL,
                "last_updated": datetime.now().isoformat(),
                "history": []
            }
            self._save_local(initial_state)
            if self.use_firestore:
                self.firestore.upsert(Config.COL_BANKROLL, "current_state", initial_state)

    def _load_local(self) -> Dict[str, Any]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_local(self, data: Dict[str, Any]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_current_bankroll(self) -> float:
        """Returns the current bankroll ready for the NEXT prediction."""
        try:
            # Sync with Firestore for multi-device parity
            if self.use_firestore:
                fs_data = self.firestore.get_document(Config.COL_BANKROLL, "current_state")
                if fs_data:
                    self._save_local(fs_data)
                    return float(fs_data.get("current_bankroll", Config.INITIAL_BANKROLL))
            
            data = self._load_local()
            return float(data.get("current_bankroll", Config.INITIAL_BANKROLL))
        except Exception as e:
            logger.error(f"Error fetching bankroll: {e}")
            return Config.INITIAL_BANKROLL

    def add_transaction(self, meeting_id: str, net_pnl: float, description: str = "") -> float:
        """
        Updates the bankroll with new PnL after a meeting settlement.
        """
        try:
            data = self._load_local()
            
            # Prevent double-counting the exact same meeting
            if any(h.get("meeting_id") == meeting_id for h in data.get("history", [])):
                logger.warning(f"Bankroll already updated for meeting {meeting_id}. Skipping.")
                return data["current_bankroll"]

            old_bankroll = data.get("current_bankroll", Config.INITIAL_BANKROLL)
            new_bankroll = old_bankroll + net_pnl
            
            # Record keeping
            transaction = {
                "meeting_id": meeting_id,
                "timestamp": datetime.now().isoformat(),
                "pnl": net_pnl,
                "description": description,
                "bankroll_after": new_bankroll
            }
            
            data["current_bankroll"] = new_bankroll
            data["high_water_mark"] = max(data.get("high_water_mark", old_bankroll), new_bankroll)
            data["last_updated"] = datetime.now().isoformat()
            
            data.setdefault("history", []).append(transaction)
            
            # Persist
            self._save_local(data)
            if self.use_firestore:
                self.firestore.upsert(Config.COL_BANKROLL, "current_state", data)
                
            logger.info(f"💰 BANKROLL UPDATED: ${old_bankroll:,.2f} -\u003e ${new_bankroll:,.2f} (PnL: ${net_pnl:,.2f})")
            return new_bankroll
            
        except Exception as e:
            logger.error(f"CRITICAL: Failed to write bankroll transaction: {e}")
            return Config.INITIAL_BANKROLL
