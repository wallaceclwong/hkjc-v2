import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def test_stable_model():
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=Config.GCP_LOCATION
    )
    
    model = "publishers/google/models/gemini-1.0-pro-001"
    train_data_uri = f"gs://{Config.GCS_BUCKET_NAME}/tuning/tuning_subset_1000.jsonl"
    
    print(f"Testing model: {model}")
    try:
        tuning_config = types.CreateTuningJobConfig(
            epoch_count=1,
            batch_size=1,
            tuned_model_display_name="test_tuning_stability"
        )
        
        job = client.tunings.tune(
            base_model=model,
            training_dataset=types.TuningDataset(gcs_uri=train_data_uri),
            config=tuning_config
        )
        print(f"SUCCESS: {model} is tunable! Job ID: {job.name}")
        return model
    except Exception as e:
        print(f"FAILED: {model}. Error: {e}")
    return None

if __name__ == "__main__":
    test_stable_model()
