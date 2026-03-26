import paramiko
import os
from pathlib import Path

def sync_vm():
    host = "45.32.255.155"
    user = "root"
    password = "6{tJs[Dhe,jv3@_G"

    print(f"--- HKJC VM SYNC ({host}) ---")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, password=password, timeout=20)
        print("Connected! Locating hkjc directory...")
        
        def safe_decode(b):
            return b.decode('utf-8', errors='ignore').strip()
        
        # 1. Check Crontab for clues
        print("Checking crontab for clues...")
        stdin, stdout, stderr = client.exec_command("crontab -l 2>/dev/null")
        cron = safe_decode(stdout.read())
        if cron:
            print(f"--- Crontab ---\n{cron}")

        # 2. Search for unique project files
        print("Searching for unique project files (daily_update.sh, prediction_engine.py)...")
        discovery_cmd = "find /opt /root /home /var -maxdepth 4 \( -name 'daily_update.sh' -o -name 'prediction_engine.py' \) 2>/dev/null | head -n 1"
        stdin, stdout, stderr = client.exec_command(discovery_cmd)
        res = safe_decode(stdout.read())
        
        project_dirs = []
        if res:
            path = Path(res)
            p_dir = path.parent.parent.as_posix() if "hkjc-automation" in res else path.parent.as_posix()
            project_dirs.append(p_dir)
        
        # Add /opt/hkjc if it exists and wasn't found
        stdin, stdout, stderr = client.exec_command("ls -d /opt/hkjc 2>/dev/null")
        opt_hkjc = safe_decode(stdout.read())
        if opt_hkjc and opt_hkjc not in project_dirs:
            project_dirs.append(opt_hkjc)

        if not project_dirs:
            print("Error: Could not find any project directories on VM.")
            return

        print(f"Found project directories: {project_dirs}")
        
        for p_dir in project_dirs:
            print(f"\n--- Syncing {p_dir} ---")
            commands = [
                f"cd {p_dir} && git pull origin main",
                f"pip3 install --break-system-packages -r {p_dir}/requirements.txt",
            ]
            
            # Additional logic for sentinel-racing
            if "sentinel-racing" in p_dir:
                commands.append("pkill -f uvicorn || true")
                commands.append(f"cd {p_dir} && nohup python3 -m uvicorn dashboard.server:app --host 0.0.0.0 --port 8080 > /root/vultr_dashboard.log 2>&1 &")
            
            for cmd in commands:
                print(f"\nRunning: {cmd}")
                stdin, stdout, stderr = client.exec_command(cmd)
                
                if "nohup" not in cmd:
                    out = safe_decode(stdout.read())
                    err = safe_decode(stderr.read())
                    if out: print(f"STDOUT: {out}")
                    if err: print(f"STDERR: {err}")
                else:
                    print("Service restarted in background.")

        print("\nSync Complete! VM is now running the latest code and features.")
            
    except Exception as e:
        print(f"Sync failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    sync_vm()
