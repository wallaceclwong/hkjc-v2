"""
Attempt to fix Firestore permissions programmatically
This requires the current user to have IAM admin rights
"""
import subprocess
import sys

print("="*60)
print("FIRESTORE PERMISSION FIX")
print("="*60)

SERVICE_ACCOUNT = "hkjc-backend@hkjc-v2.iam.gserviceaccount.com"
PROJECT_ID = "hkjc-v2"
REQUIRED_ROLES = [
    "roles/datastore.user",
    "roles/aiplatform.user"
]

print(f"\nService Account: {SERVICE_ACCOUNT}")
print(f"Project: {PROJECT_ID}")
print(f"\nRequired Roles:")
for role in REQUIRED_ROLES:
    print(f"  - {role}")

print("\n" + "-"*60)
print("Attempting to grant permissions...")
print("-"*60)

for role in REQUIRED_ROLES:
    print(f"\nGranting {role}...")
    
    cmd = [
        "gcloud", "projects", "add-iam-policy-binding", PROJECT_ID,
        f"--member=serviceAccount:{SERVICE_ACCOUNT}",
        f"--role={role}",
        "--quiet"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"  [OK] Successfully granted {role}")
        else:
            print(f"  [FAIL] {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] Command took too long")
    except FileNotFoundError:
        print(f"  [ERROR] gcloud CLI not found or not in PATH")
        print("\nAlternative: Fix manually in GCP Console")
        print("1. Go to: https://console.cloud.google.com/iam-admin/iam?project=hkjc-v2")
        print(f"2. Find: {SERVICE_ACCOUNT}")
        print("3. Click Edit (pencil icon)")
        print("4. Add roles:")
        for r in REQUIRED_ROLES:
            print(f"   - {r}")
        sys.exit(1)
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "="*60)
print("Testing Firestore connection...")
print("="*60)

try:
    from google.cloud import firestore
    db = firestore.Client(project=PROJECT_ID)
    
    # Try to write a test document
    test_ref = db.collection("_health_check").document("test")
    test_ref.set({"timestamp": firestore.SERVER_TIMESTAMP, "status": "ok"})
    
    # Try to read it back
    doc = test_ref.get()
    
    if doc.exists:
        print("\n[SUCCESS] Firestore is now working!")
        print("Cloud sync enabled.")
    else:
        print("\n[FAIL] Could not verify Firestore access")
        
except Exception as e:
    print(f"\n[FAIL] Firestore still not accessible: {e}")
    print("\nYou may need to:")
    print("1. Wait a few minutes for IAM changes to propagate")
    print("2. Fix permissions manually in GCP Console")

print("\n" + "="*60)
