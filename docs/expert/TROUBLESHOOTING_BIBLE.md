# Expert Guide: Troubleshooting Bible (HKJC-V2)

This document is the "Technical Immune System" of the project—a collection of fixes for the most common errors encountered during development.

## 1. "The Blank Dashboard" (Port 8000)
- **Symptom**: Localhost loads, but only shows "Loading picks..." or a blank table.
- **Root Cause**: A "Corrupted" prediction file with a non-standard date (like "test") in `data/predictions/`.
- **Expert Fix**:
    1. Scan `data/predictions/` for any file not matching `YYYY-MM-DD`.
    2. Delete the offending test file.
    3. Restart the FastAPI server.

## 2. Firestore 403 (Permission Denied)
- **Symptom**: "Error 403: The caller does not have permission."
- **Root Cause**: Service account credentials expired or IAM roles missing.
- **Expert Fix**:
    1. Verify `GOOGLE_APPLICATION_CREDENTIALS` points to `service-account-key.json`.
    2. Run `python fix_firestore_permissions.py` (if available) or check IAM in GCP Console.
    3. Re-authenticate via `gcloud auth application-default login`.

## 3. HKJC Layout Changes (Fetcher Errors)
- **Symptom**: "Element not found" or "Scraping failed" in `auto_fetch_racecards.py`.
- **Root Cause**: HKJC updated their CSS selectors or URL structure.
- **Expert Fix**: 
    1. Open `services/browser_manager.py`.
    2. Check if the selectors for "Race Index" or "Dividend Table" still match the live site.
    3. Update the `selectors` dictionary.

## 4. PowerShell Execution Policy
- **Symptom**: `gcloud` or `.bat` files fail with `UnauthorizedAccess`.
- **Root Cause**: Windows default security policy prevents script execution.
- **Expert Fix**: 
    1. Open PowerShell as Admin.
    2. Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

---
> [!TIP]
> If a future AI is stumped, always check the **`data/logs/`** folder first. 90% of issues are resolved by reading the direct traceback in the log files.
