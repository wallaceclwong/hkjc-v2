import paramiko

def send_brief(host, user, password, token, chat_id):
    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        
        # Construct the mock brief script
        # Note: We use triple quotes and f-strings carefully
        script = f"""
import requests
token = "{token}"
chat_id = "{chat_id}"
url = f"https://api.telegram.org/bot{{token}}/sendMessage"
payload = {{
    "chat_id": chat_id,
    "text": "🚀 *ULTIMATE ELITE BRIEF: TEST-RACE-8*\\n🎯 *Pick:* LUNAR CHAMPION (#3)\\n📊 *EV:* 4.25\\n\\n🧠 *Strategic Reasoning:*\\nHigh sectional flash detected (5.2L gain last 400m). Jockey Purton is at 18% win rate for this distance. Track bias favors Barrier 3 (79% win rate).\\n\\n*Verdict:* High Confidence (88%).",
    "parse_mode": "Markdown"
}}
r = requests.post(url, json=payload)
print(r.status_code)
print(r.text)
"""
        # Save and run on VM
        stdin, stdout, stderr = ssh.exec_command(f"python3 -c '{script}'")
        print("Output:")
        print(stdout.read().decode())
        print("Error (if any):")
        print(stderr.read().decode())
        
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_brief("45.32.255.155", "root", "6{tJs[Dhe,jv3@_G", "8737809557:AAHJhHp8HxtMuY8higwt-enpu8bjWugvn2s", "1112043264")
