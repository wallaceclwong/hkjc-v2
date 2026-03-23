import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config

def test_vertex_connectivity():
    print(f"Testing Vertex AI Connectivity...")
    model_id = "gemini-2.5-pro"
    print(f"Model: {model_id}")
    
    try:
        client = genai.Client(
            vertexai=True,
            project=Config.PROJECT_ID,
            location=Config.GCP_LOCATION
        )
        
        response = client.models.generate_content(
            model=model_id,
            contents="Say 'Vertex AI Pro Active' if you can read this."
        )
        
        print("\n--- Response ---")
        print(response.text)
        print("----------------")
        
        if "Vertex AI Pro Active" in response.text:
            print("\nSUCCESS: AI Pro plan is active and bypassing regional blocks!")
        else:
            print("\nWARNING: Unexpected response, but connectivity established.")
            
    except Exception as e:
        print(f"\nFAILED: Error connecting to Vertex AI: {e}")

if __name__ == "__main__":
    test_vertex_connectivity()
