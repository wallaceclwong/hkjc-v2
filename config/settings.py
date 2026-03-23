import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hkjc-v2-3026-63")
    REGION = os.getenv("GCP_REGION", "asia-east1")
    FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "(default)")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # AI Config
    GEMINI_MODEL = "gemini-2.5-pro"
    USE_VERTEX_AI = True               # Vertex AI
    GCP_LOCATION = "us-central1"       # Models are confirmed available here
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "hkjc-v2-vault")
    
    # --- Betting Account (User must fill these in .env) ---
    HKJC_ACCOUNT = os.getenv("HKJC_ACCOUNT", "YOUR_ACCOUNT_ID")
    HKJC_PASSWORD = os.getenv("HKJC_PASSWORD", "YOUR_PASSWORD")
    
    # --- Prediction Settings ---
    BROWSER_TIMEOUT = 30000  # 30 seconds
    
    # Kelly Criterion Config
    INITIAL_BANKROLL = 10000.0
    KELLY_FRACTION = 0.25  # "Quarter-Kelly" for safer growth
    
    # Collections
    COL_FIXTURES = "fixtures"
    COL_RACECARDS = "racecards"
    COL_ODDS = "odds"
    COL_PREDICTIONS = "predictions"
    COL_ANALYTICAL = "analytical"
    COL_RESULTS = "results"
    COL_WEATHER = "weather"

    # Backfill Config
    BACKFILL_BATCH_SIZE = 5
    BACKFILL_DELAY = 5000  # 5 seconds between meetings

    @classmethod
    def get_firestore_client(cls):
        from google.cloud import firestore
        if cls.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            return firestore.Client(project=cls.PROJECT_ID, database=cls.FIRESTORE_DATABASE, credentials=None) # Client will pick up from env if set
        return firestore.Client(project=cls.PROJECT_ID, database=cls.FIRESTORE_DATABASE)
