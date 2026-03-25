import os
import sys
from google import genai

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

client = genai.Client(
    vertexai=True,
    project=Config.PROJECT_ID,
    location=Config.GCP_LOCATION
)

print("Client attributes:", dir(client))
if hasattr(client, "models"):
    print("Models attributes:", dir(client.models))
if hasattr(client, "tunings"):
    print("Tunings attributes:", dir(client.tunings))
if hasattr(client, "tunes"):
    print("Tunes attributes:", dir(client.tunes))
