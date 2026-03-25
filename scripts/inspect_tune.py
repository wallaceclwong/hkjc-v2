from google import genai
import inspect
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Config

client = genai.Client(
    vertexai=True,
    project=Config.PROJECT_ID,
    location=Config.GCP_LOCATION
)

print("Signature of client.tunings.tune:")
print(inspect.signature(client.tunings.tune))
