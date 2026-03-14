import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hkjc-v2-main")
    REGION = os.getenv("GCP_REGION", "asia-east1")
    FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "(default)")
    
    # AI Config
    GEMINI_MODEL = "gemini-1.5-pro-latest"
    
    # Ingestion Config
    BROWSER_TIMEOUT = 30000  # 30 seconds
    
    # Collections
    COL_FIXTURES = "fixtures"
    COL_RACECARDS = "racecards"
    COL_ODDS = "odds"
    COL_PREDICTIONS = "predictions"
    COL_RESULTS = "results"
    COL_WEATHER = "weather"
