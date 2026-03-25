import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def test_gemini_api_tuning():
    print("Initializing Gemini API Client (non-Vertex)...")
    client = genai.Client(
        api_key=Config.GEMINI_API_KEY
    )
    
    # In Gemini API (non-Vertex), model names for tuning are often different
    # or don't require the publishers/google/models prefix.
    model = "models/gemini-1.5-flash-001"
    
    # However, Gemini API tuning usually requires data in GCS (for Vertex) 
    # OR a different data format (for AI Studio).
    # Since we are using the genai SDK, it might handle both.
    
    print(f"Testing Gemini API Tuning with {model}...")
    try:
        # Note: Tuning via API Key might have different requirements
        job = client.models.tune(
            base_model=model,
            training_dataset=types.TuningDataset(
                gcs_uri=f"gs://{Config.GCS_BUCKET_NAME}/tuning/tuning_subset_1000.jsonl"
            ),
            config=types.CreateTuningJobConfig(
                epoch_count=1,
                batch_size=4,
                tuned_model_display_name="test_api_tuning"
            )
        )
        print(f"SUCCESS: {model} is tunable via Gemini API! Job ID: {job.name}")
        return True
    except Exception as e:
        print(f"FAILED: {model} via Gemini API. Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_api_tuning()
