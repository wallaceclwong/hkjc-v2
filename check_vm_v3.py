import paramiko
import sys

def check_vm(host, user, password):
    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Connected!")
        
        # Check root directory
        stdin, stdout, stderr = ssh.exec_command("ls -F /root")
        print("\n--- /root contents ---")
        root_files = stdout.read().decode().splitlines()
        for f in root_files:
            print(f"  {f}")
        
        # Check if hkjc exists
        print("\n--- Searching for hkjc ---")
        stdin, stdout, stderr = ssh.exec_command("find /root -name 'hkjc' -type d")
        found = stdout.read().decode().splitlines()
        if found:
            for path in found:
                print(f"✅ FOUND: {path}")
        else:
            print("❌ NOT FOUND: hkjc")

        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_vm("45.32.255.155", "root", "6{tJs[Dhe,jv3@_G")
