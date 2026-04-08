import paramiko

def update_env(host, user, password, token, chat_id):
    print(f"Updating .env on {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        sftp = ssh.open_sftp()
        
        # Read existing .env
        env_path = "/root/ultimate_engine/.env"
        try:
            with sftp.open(env_path, 'r') as f:
                content = f.read().decode()
        except FileNotFoundError:
            content = ""
            
        # Append new keys if missing
        if "TELEGRAM_BOT_TOKEN" not in content:
            content += f"\nTELEGRAM_BOT_TOKEN={token}"
        if "TELEGRAM_CHAT_ID" not in content:
            content += f"\nTELEGRAM_CHAT_ID={chat_id}"
            
        with sftp.open(env_path, 'w') as f:
            f.write(content)
            
        print("VM .env updated successfully.")
        sftp.close()
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_env("45.32.255.155", "root", "6{tJs[Dhe,jv3@_G", "8737809557:AAHJhHp8HxtMuY8higwt-enpu8bjWugvn2s", "1112043264")
