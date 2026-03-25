import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def check_tuning_status():
    client = genai.Client(
        vertexai=True,
        project="386233903900",
        location=Config.GCP_LOCATION
    )
    
    print("Listing recent tuning jobs...")
    try:
        jobs = list(client.tunings.list())
        for job in jobs:
            print(f"Name: {job.name}")
            # Try different potential display name attributes
            display_name = getattr(job, "display_name", "N/A")
            if display_name == "N/A":
                display_name = getattr(job, "tuned_model_display_name", "N/A")
            
            print(f"  Display Name Identifier: {display_name}")
            print(f"  State: {job.state}")
            print(f"  Create Time: {getattr(job, 'create_time', 'N/A')}")
            print("-" * 30)
    except Exception as e:
        print(f"Failed to list jobs: {e}")

if __name__ == "__main__":
    check_tuning_status()
