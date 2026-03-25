import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def check_tuning_status():
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=Config.GCP_LOCATION
    )
    
    print("Listing recent tuning jobs...")
    try:
        # We listing tuning jobs. In genai SDK, it's client.tunings.list()
        for job in client.tunings.list():
            print(f"Name: {job.name}")
            print(f"Display Name: {job.display_name}")
            print(f"State: {job.state}")
            print(f"Created: {job.create_time}")
            print("-" * 30)
    except Exception as e:
        print(f"Failed to list jobs: {e}")

if __name__ == "__main__":
    check_tuning_status()
