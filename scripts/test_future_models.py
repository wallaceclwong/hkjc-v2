import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def test_future_models():
    client = genai.Client(
        vertexai=True,
        project="386233903900",
        location=Config.GCP_LOCATION
    )
    
    # Try models that appeared in our 'list' earlier even without 'tune' action
    models_to_test = [
        "publishers/google/models/gemini-2.5-flash",
        "publishers/google/models/gemini-2.0-flash",
        "publishers/google/models/gemini-1.5-flash" # The stable alias
    ]
    
    train_data_uri = f"gs://{Config.GCS_BUCKET_NAME}/tuning/tuning_subset_1000.jsonl"
    
    for model in models_to_test:
        print(f"Testing model: {model}")
        try:
            tuning_config = types.CreateTuningJobConfig(
                epoch_count=1,
                batch_size=1,
                tuned_model_display_name="test_future_model"
            )
            job = client.tunings.tune(
                base_model=model,
                training_dataset=types.TuningDataset(gcs_uri=train_data_uri),
                config=tuning_config
            )
            print(f"SUCCESS: {model} is tunable!")
            return model
        except Exception as e:
            print(f"FAILED: {model}. Error: {e}")
    return None

if __name__ == "__main__":
    test_future_models()
