import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config

def test_standard_connectivity():
    print(f"Testing Standard API Connectivity with NEW SDK...")
    model_id = "gemini-1.5-flash"
    print(f"Model: {model_id}")
    
    try:
        # Standard route using API Key
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model_id,
            contents="Say 'Standard API Pro Active' if you can read this."
        )
        
        print("\n--- Response ---")
        print(response.text)
        print("----------------")
        
        if "Standard API Pro Active" in response.text:
            print("\nSUCCESS: Standard API is working with the new SDK!")
        else:
            print("\nWARNING: Unexpected response.")
            
    except Exception as e:
        print(f"\nFAILED: Error connecting via Standard API: {e}")

if __name__ == "__main__":
    test_standard_connectivity()
