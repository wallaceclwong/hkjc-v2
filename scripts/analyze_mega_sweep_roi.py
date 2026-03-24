import sys
import os
import json
from pathlib import Path
from google.cloud import storage

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def analyze_roi():
    print("Initializing GCS Client...")
    client = storage.Client(project=Config.PROJECT_ID)
    bucket_name = 'hkjc-v2-vault'
    prefix = 'batch_output/prediction-hkjc-v2-2026-03-22T02:00:00Z/'
    
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    if not blobs:
        print("No output files found!")
        return

    print(f"Found {len(blobs)} output files. Sampling first 5 for ROI estimate...")
    
    total_races = 0
    unit_total_return = 0.0
    kelly_total_return = 0.0
    initial_bankroll = 10000.0
    current_bankroll = initial_bankroll
    
    for blob in blobs[:5]:
        content = blob.download_as_text()
        for line in content.splitlines():
            if not line.strip(): continue
            data = json.loads(line)
            
            # Structure check based on Vertex AI Batch Prediction
            # Note: actual fields depend on the model output schema
            prediction = data.get('prediction', {})
            instance = data.get('instance', {})
            
            # Simplified Logic for Estimation:
            # We assume 'prediction' contains a score for the 'win' outcome
            # and 'instance' contains the actual result and odds (if passed)
            # Since we don't have the exact schema here, we'll look for keywords
            
            total_races += 1
            
            # TO BE REFINED once schema is viewed
            # Logic: If prediction > threshold and result == win: profit
            
    print(f"Analysis of {total_races} races complete.")
    # More detailed printing here once schema is confirmed

if __name__ == "__main__":
    analyze_roi()
