import paramiko

def check_deps(host, user, password):
    print(f"Checking dependencies on {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        
        # Check if python3 -c "import httpx; import pydantic" works
        cmd = "python3 -c \"import httpx; import pydantic; print('DEPS OK')\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if out == "DEPS OK":
            print("✅ Dependencies are installed on VM.")
        else:
            print("❌ Dependencies missing or error:")
            print(err)
            
            # Try to install them if missing
            print("Attempting to install missing dependencies...")
            stdin, stdout, stderr = ssh.exec_command("pip3 install httpx pydantic loguru python-dotenv")
            print(stdout.read().decode())
            print(stderr.read().decode())
            
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_deps("45.32.255.155", "root", "6{tJs[Dhe,jv3@_G")
