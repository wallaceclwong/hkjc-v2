import paramiko
import os

def bootstrap():
    host = "45.32.255.155"
    user = "root"
    password = "6{tJs[Dhe,jv3@_G"

    print(f"Connecting to {host} for Direct Deployment...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, password=password, timeout=20)
        print("Connected! Initializing Fast-Deploy...")
        
        commands = [
            "apt-get update && apt-get install -y python3-pip",
            "pip3 install --break-system-packages -r /root/hkjc/requirements.txt",
            "python3 -m playwright install --with-deps chromium",
            "sed -i 's|GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=/root/hkjc/service-account-key.json|' /root/hkjc/.env",
            "ufw allow 8080/tcp",
            "cd /root/hkjc && pkill -f uvicorn || true",
            "cd /root/hkjc && nohup python3 -m uvicorn dashboard.server:app --host 0.0.0.0 --port 8080 > /root/vultr_dashboard.log 2>&1 &"
        ]
        
        for cmd in commands:
            print(f"\n--- {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            # We don't wait for the last command (nohup)
            if "nohup" not in cmd:
                out = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                if out: print(out)
                if err: print(f"STDERR: {err}")
            else:
                print("Server launched in background.")
            
    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    bootstrap()
