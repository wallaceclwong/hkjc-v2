import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def test_region(location):
    print(f"Testing Region: {location}")
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=location
    )
    
    # Try gemini-1.5-flash-001 which is very stable for tuning
    model = "publishers/google/models/gemini-1.5-flash-001"
    train_data_uri = f"gs://{Config.GCS_BUCKET_NAME}/tuning/tuning_subset_1000.jsonl"
    
    try:
        tuning_config = types.CreateTuningJobConfig(
            epoch_count=1,
            batch_size=1,
            tuned_model_display_name=f"test_region_{location.replace('-', '_')}"
        )
        
        job = client.tunings.tune(
            base_model=model,
            training_dataset=types.TuningDataset(gcs_uri=train_data_uri),
            config=tuning_config
        )
        print(f"SUCCESS in {location}: Job ID: {job.name}")
        return True
    except Exception as e:
        print(f"FAILED in {location}. Error: {e}")
        return False

if __name__ == "__main__":
    # Test common tuning regions
    for loc in ["europe-west4", "us-east4", "asia-northeast1"]:
        if test_region(loc):
            break
