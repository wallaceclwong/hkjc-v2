# Firestore Permission Fix Guide

## Quick Fix (5 minutes)

### Step 1: Open GCP Console
Go to: https://console.cloud.google.com/iam-admin/iam?project=hkjc-v2

### Step 2: Find Service Account
Look for: `hkjc-backend@hkjc-v2.iam.gserviceaccount.com`

### Step 3: Edit Permissions
1. Click the **pencil icon** (Edit) next to the service account
2. Click **"+ ADD ANOTHER ROLE"**
3. Search for and add: **"Cloud Datastore User"**
4. Click **"+ ADD ANOTHER ROLE"** again
5. Search for and add: **"DeepSeek AI User"**
6. Click **"SAVE"**

### Step 4: Wait & Test
1. Wait 1-2 minutes for changes to propagate
2. Run: `python test_firestore_connection.py`

---

## Alternative: Use Firestore in Native Mode

If you don't want to fix permissions, the system works perfectly in local mode.

---

## Verification

After fixing, you should see:
```
[OK] Firestore connected and working
```

Instead of:
```
[ERROR] 403 Missing or insufficient permissions
```
