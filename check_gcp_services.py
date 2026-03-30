import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

print("="*60)
print("GOOGLE CLOUD SERVICES CHECK")
print("="*60)

# 1. Check environment variables
print("\n1. Environment Variables:")
project_id = os.getenv("GCP_PROJECT_ID")
print(f"   GCP_PROJECT_ID: {project_id if project_id else '[NOT SET]'}")

# 2. Check Firestore connection
print("\n2. Firestore Connection:")
try:
    from google.cloud import firestore
    db = firestore.Client(project=project_id if project_id else "hkjc-v2")
    
    # Try to read a document
    test_ref = db.collection("_health_check").document("test")
    test_ref.set({"timestamp": firestore.SERVER_TIMESTAMP, "status": "ok"})
    doc = test_ref.get()
    
    if doc.exists:
        print("   [OK] Firestore connected and working")
        print(f"   Project: {db.project}")
    else:
        print("   [WARN] Firestore connected but test write failed")
        
except Exception as e:
    print(f"   [ERROR] Firestore connection failed: {e}")

# 3. Check Vertex AI credentials
print("\n3. Vertex AI Setup:")
try:
    import vertexai
    from config.settings import Config
    
    vertexai.init(project=Config.PROJECT_ID, location=Config.GCP_LOCATION)
    print(f"   [OK] Vertex AI initialized")
    print(f"   Project: {Config.PROJECT_ID}")
    print(f"   Region: {Config.REGION}")
    print(f"   Model: {Config.GEMINI_MODEL}")
    
except Exception as e:
    print(f"   [ERROR] Vertex AI setup failed: {e}")

# 4. Check credentials file
print("\n4. Service Account Credentials:")
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if cred_path:
    print(f"   Path: {cred_path}")
    if os.path.exists(cred_path):
        print("   [OK] Credentials file exists")
        
        # Check file size
        size = os.path.getsize(cred_path)
        print(f"   Size: {size} bytes")
    else:
        print("   [ERROR] Credentials file not found")
else:
    print("   [WARN] GOOGLE_APPLICATION_CREDENTIALS not set")

# 5. Test a simple prediction call (if possible)
print("\n5. Vertex AI Model Test:")
try:
    from vertexai.generative_models import GenerativeModel
    from config.settings import Config
    
    model = GenerativeModel(Config.GEMINI_MODEL)
    print(f"   [OK] Model loaded: {Config.GEMINI_MODEL}")
    print("   [INFO] Skipping actual API call to avoid charges")
    
except Exception as e:
    print(f"   [ERROR] Model loading failed: {e}")

print("\n" + "="*60)
print("CHECK COMPLETE")
print("="*60)
