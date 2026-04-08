import paramiko
import os
from pathlib import Path

def sync_local_to_vm(host, user, password):
    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    sftp = ssh.open_sftp()

    # Source Mapping (Local path -> Remote path)
    sync_map = {
        "c:/Users/ASUS/ultimate_engine/consensus_agent.py": "/root/ultimate_engine/consensus_agent.py",
        "c:/Users/ASUS/ultimate_engine/ultimate_scheduler_vm.py": "/root/ultimate_engine/ultimate_scheduler_vm.py",
        "c:/Users/ASUS/ultimate_engine/models/schemas.py": "/root/ultimate_engine/models/schemas.py",
        "c:/Users/ASUS/ultimate_engine/services/racecard_ingest.py": "/root/ultimate_engine/services/racecard_ingest.py",
        "c:/Users/ASUS/ultimate_engine/services/live_audit_service.py": "/root/ultimate_engine/services/live_audit_service.py",
        "c:/Users/ASUS/ultimate_engine/tests/test_live_reasoning.py": "/root/ultimate_engine/tests/test_live_reasoning.py",
        "c:/Users/ASUS/ultimate_engine/tests/test_scheduler_filtering.py": "/root/ultimate_engine/tests/test_scheduler_filtering.py",
        "c:/Users/ASUS/hkjc/midweek_audit_r11.py": "/root/ultimate_engine/midweek_audit_r11.py",
        "c:/Users/ASUS/hkjc/data/racecard_20260406_R11.json": "/root/ultimate_engine/data/racecard_20260406_R11.json"
    }

    for l_path_str, r_path in sync_map.items():
        l_path = Path(l_path_str)
        
        # Ensure remote directory exists
        r_dir = os.path.dirname(r_path)
        ssh.exec_command(f"mkdir -p {r_dir}")
        
        print(f"Syncing {l_path.name}...")
        sftp.put(str(l_path), r_path)

    sftp.close()
    ssh.close()
    print("Sync complete.")

if __name__ == "__main__":
    sync_local_to_vm(
        "45.32.255.155",
        "root",
        "6{tJs[Dhe,jv3@_G"
    )
