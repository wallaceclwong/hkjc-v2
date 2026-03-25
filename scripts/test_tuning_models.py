import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def test_models():
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=Config.GCP_LOCATION
    )
    
    # Try multiple common stable models
    models_to_test = [
        "publishers/google/models/gemini-1.5-flash-001",
        "publishers/google/models/gemini-1.5-flash-002",
        "publishers/google/models/gemini-1.0-pro-001",
        "publishers/google/models/gemini-1.5-pro-001"
    ]
    
    train_data_uri = f"gs://{Config.GCS_BUCKET_NAME}/tuning/tuning_subset_1000.jsonl"
    
    for model in models_to_test:
        print(f"Testing model: {model}")
        try:
            # We just try to initiate the call. We won't actually finish if we get 400.
            # Use very minimal config to speed up check
            job = client.tunings.tune(
                base_model=model,
                training_dataset=types.TuningDataset(gcs_uri=train_data_uri),
                config=types.CreateTuningJobConfig(
                    epoch_count=1,
                    batch_size=1
                ),
                display_name=f"test_launch_{model.split('/')[-1].replace('.', '_')}"
            )
            print(f"SUCCESS: {model} is tunable! Job ID: {job.name}")
            # If successful, we DON'T want to keep it running for now as it's a test.
            # But we can just stop here.
            return model
        except Exception as e:
            print(f"FAILED: {model}. Error: {e}")
            print("-" * 30)
    return None

if __name__ == "__main__":
    test_models()
