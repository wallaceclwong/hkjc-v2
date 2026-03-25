import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def list_models_for_tuning(location):
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=location
    )
    print(f"--- Listing models in {location} ---")
    try:
        # Using client.models.list()
        # The list method returns an iterable of Model objects
        models = list(client.models.list())
        for model in models:
            actions = getattr(model, "supported_actions", [])
            if actions is None: 
                actions = []
            
            is_tunable = "tune" in [a.lower() for a in actions]
            if is_tunable:
                print(f"Model: {model.name} (TUNABLE)")
            else:
                # Still print if it looks like a Gemini model
                if "gemini" in model.name.lower():
                    print(f"Model: {model.name} (Not tunable here, actions: {actions})")
    except Exception as e:
        print(f"Failed to list models in {location}: {e}")

if __name__ == "__main__":
    list_models_for_tuning("us-central1")
    # list_models_for_tuning("asia-east1")
