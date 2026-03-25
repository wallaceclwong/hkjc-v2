import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def list_gemini_15_for_tuning(location):
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=location
    )
    print(f"--- Gemini 1.5 Models in {location} ---")
    try:
        models = list(client.models.list())
        for model in models:
            if "gemini-1.5" in model.name.lower():
                actions = getattr(model, "supported_actions", [])
                if actions is None: 
                    actions = []
                
                is_tunable = "tune" in [a.lower() for a in actions]
                print(f"Model: {model.name} - Tunable: {is_tunable} - Actions: {actions}")
    except Exception as e:
        print(f"Error in {location}: {e}")

if __name__ == "__main__":
    list_gemini_15_for_tuning("us-central1")
    list_gemini_15_for_tuning("asia-east1")
