import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def debug_project_resolution():
    project_id = "project-6172aadc-bdc0-43ee-8ac"
    # Project number will be filled based on gcloud output if needed
    
    locations = ["us-central1"]
    
    for loc in locations:
        print(f"--- Testing Project ID in {loc} ---")
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=loc
        )
        # Deep inspection
        try:
            # For genai SDK, we check internal _api_client
            api_client = client.compute._api_client
            print(f"Internal API Project: {api_client.project}")
            print(f"Internal API Location: {api_client.location}")
            
            m = client.models.get(model='publishers/google/models/gemini-1.5-flash-001')
            print(f"SUCCESS: Found model! Actions: {m.supported_actions}")
        except Exception as e:
            print(f"FAILED with ID: {e}")
            
if __name__ == "__main__":
    debug_project_resolution()
