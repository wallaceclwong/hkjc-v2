import os
import shutil
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta

def get_dir_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def clean_old_files(days=30, dry_run=False):
    print(f"\n[6/6] Checking for old data files (> {days} days)...")
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    if not data_dir.exists():
        return 0

    reclaimed_bytes = 0
    cutoff = time.time() - (days * 24 * 3600)
    
    # We scan predictions, racecards, results, odds, weather
    folders = ["predictions", "racecards", "results", "odds", "weather"]
    for folder in folders:
        target = data_dir / folder
        if not target.exists(): continue
        
        print(f"  Scanning {folder}...")
        for f in target.glob("*.json"):
            if f.stat().st_mtime < cutoff:
                size = f.stat().st_size
                print(f"    Removing old data: {folder}/{f.name} ({size / 1024:.1f} KB)")
                reclaimed_bytes += size
                if not dry_run:
                    try: f.unlink()
                    except: pass
    
    return reclaimed_bytes

def clean_agent_artifacts(dry_run=False):
    print("\n[5/6] Checking AI Agent Artifacts...")
    # Dynamically find the brain directory
    user_profile = os.environ.get("USERPROFILE")
    if not user_profile:
        print("  Error: Could not find USERPROFILE environment variable.")
        return 0
    
    brain_dir = Path(user_profile) / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        print(f"  Note: Artifact directory not found at {brain_dir}")
        return 0

    reclaimed_bytes = 0
    print(f"  Scanning: {brain_dir}...")
    
    # We target large media files across ALL session directories
    media_extensions = [".webp", ".png", ".mp4", ".mov"]
    
    try:
        for session_dir in brain_dir.iterdir():
            if session_dir.is_dir():
                for p in session_dir.iterdir():
                    if p.suffix.lower() in media_extensions:
                        size = p.stat().st_size
                        print(f"    Removing agent media: {session_dir.name}/{p.name} ({size / 1024 / 1024:.1f} MB)")
                        reclaimed_bytes += size
                        if not dry_run:
                            try: p.unlink()
                            except: pass
    except Exception as e:
        print(f"  Warning: Could not fully scan agent directory: {e}")

    return reclaimed_bytes

def deep_clean(dry_run=False, include_agent=False, retention_days=None):
    print(f"--- HKJC DEEP CLEAN ---")
    if dry_run: print("[DRY RUN] No files will be deleted.")

    base_dir = Path(__file__).resolve().parent.parent
    reclaimed_bytes = 0

    # 1. Clean __pycache__
    print("\n[1/6] Cleaning Python caches...")
    for p in base_dir.rglob("__pycache__"):
        if p.is_dir():
            size = get_dir_size(p)
            print(f"  Removing: {p.relative_to(base_dir)} ({size / 1024:.1f} KB)")
            reclaimed_bytes += size
            if not dry_run:
                try: shutil.rmtree(p)
                except Exception as e: print(f"    Error: {e}")

    # 2. Clean Browser Sessions
    print("\n[2/6] Cleaning Playwright session data...")
    data_dir = base_dir / "data"
    if data_dir.exists():
        for p in data_dir.glob("browser_session_*"):
            if p.is_dir():
                size = get_dir_size(p)
                print(f"  Removing: {p.relative_to(base_dir)} ({size / 1024 / 1024:.1f} MB)")
                reclaimed_bytes += size
                if not dry_run:
                    try: shutil.rmtree(p)
                    except Exception as e: 
                        if "lock" in str(e).lower():
                            print(f"    Skipped (Locked by active browser)")
                        else:
                            print(f"    Error: {e}")

    # 3. Clean tmp directory
    print("\n[3/6] Clearing tmp directory...")
    tmp_dir = base_dir / "tmp"
    if tmp_dir.exists():
        for p in tmp_dir.iterdir():
            size = get_dir_size(p) if p.is_dir() else p.stat().st_size
            print(f"  Removing tmp: {p.name} ({size / 1024:.1f} KB)")
            reclaimed_bytes += size
            if not dry_run:
                try:
                    if p.is_dir(): shutil.rmtree(p)
                    else: p.unlink()
                except Exception as e: print(f"    Error: {e}")

    # 4. Clean Debug Files
    print("\n[4/6] Removing scraper debug files...")
    debug_patterns = ["services/debug_*", "services/*.png", "services/*.html", "data/debug_*"]
    for pattern in debug_patterns:
        for p in base_dir.glob(pattern):
            if p.is_file():
                size = p.stat().st_size
                print(f"  Removing debug file: {p.relative_to(base_dir)} ({size / 1024:.1f} KB)")
                reclaimed_bytes += size
                if not dry_run:
                    try: p.unlink()
                    except Exception as e: print(f"    Error: {e}")

    # 5. Optional Agent Artifacts
    if include_agent:
        reclaimed_bytes += clean_agent_artifacts(dry_run)
    else:
        print("\n[5/6] Skipping AI Agent Media (use --agent to include)")

    # 6. Data Retention
    if retention_days is not None:
        reclaimed_bytes += clean_old_files(days=retention_days, dry_run=dry_run)
    else:
        print("\n[6/6] Skipping Data Retention (use --days N to include)")

    print(f"\nTotal Space Reclaimed: {reclaimed_bytes / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HKJC Deep Clean Utility")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    parser.add_argument("--agent", action="store_true", help="Clean up AI agent media recordings (.webp, .png)")
    parser.add_argument("--days", type=int, default=None, help="Delete data files older than N days")
    args = parser.parse_args()
    
    deep_clean(dry_run=args.dry_run, include_agent=args.agent, retention_days=args.days)
