from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hkjc-v2")
    REGION = os.getenv("GCP_REGION", "asia-east1")
    FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "(default)")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_PROJECT_ID = os.getenv("VERTEX_MODEL_PROJECT", PROJECT_ID)  # Consolidated: same as PROJECT_ID
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # AI Config
    TUNED_MODEL_ENDPOINT = os.getenv("TUNED_MODEL_ENDPOINT", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", TUNED_MODEL_ENDPOINT) or "gemini-2.5-flash"  # Falls back if endpoint not set
    GEMINI_MODEL_FALLBACK = "gemini-2.5-flash"  # For weather intel and non-prediction tasks
    SHADOW_MODEL = os.getenv("SHADOW_MODEL", "gemini-2.5-pro")  # A/B test: shadow model runs in parallel
    USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "True").lower() == "true"
    GCP_LOCATION = "us-central1"       # Models are confirmed available here
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "hkjc-v2-vault-316780")
    
    # --- Betting Account (User must fill these in .env) ---
    HKJC_ACCOUNT = os.getenv("HKJC_ACCOUNT", "YOUR_ACCOUNT_ID")
    HKJC_PASSWORD = os.getenv("HKJC_PASSWORD", "YOUR_PASSWORD")
    
    # --- Prediction Settings ---
    BROWSER_TIMEOUT = 30000  # 30 seconds
    
    # Kelly Criterion Config
    INITIAL_BANKROLL = 9000.0
    KELLY_FRACTION = 0.10  # "Tenth-Kelly" for safe real-money start
    
    # Collections
    COL_FIXTURES = "fixtures"
    COL_RACECARDS = "racecards"
    COL_ODDS = "odds"
    COL_PREDICTIONS = "predictions"
    COL_ANALYTICAL = "analytical"
    COL_RESULTS = "results"
    COL_WEATHER = "weather_intel"
    COL_MARKET_ALERTS = "market_alerts"
    COL_REPORTS = "meeting_reports"
    COL_BANKROLL = "bankroll"

    # Backfill Config
    BACKFILL_BATCH_SIZE = 5
    BACKFILL_DELAY = 5000  # 5 seconds between meetings

    @classmethod
    def get_firestore_client(cls):
        from google.cloud import firestore
        from google.oauth2 import service_account
        
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            print(f"[INFO] Using Service Account Key: {creds_path}")
            creds = service_account.Credentials.from_service_account_file(creds_path)
            return firestore.Client(project=cls.PROJECT_ID, database=cls.FIRESTORE_DATABASE, credentials=creds)
            
        return firestore.Client(project=cls.PROJECT_ID, database=cls.FIRESTORE_DATABASE)
