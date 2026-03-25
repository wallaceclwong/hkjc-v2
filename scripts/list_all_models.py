import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

def list_all_models(location):
    client = genai.Client(
        vertexai=True,
        project=Config.PROJECT_ID,
        location=location
    )
    print(f"--- All Models in {location} ---")
    try:
        models = list(client.models.list())
        for model in models:
            actions = getattr(model, "supported_actions", [])
            if actions is None: actions = []
            print(f"{model.name} | Actions: {actions}")
    except Exception as e:
        print(f"Error in {location}: {e}")

if __name__ == "__main__":
    list_all_models("us-central1")
