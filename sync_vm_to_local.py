import paramiko
import os
from stat import S_ISDIR

def download_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for entry in sftp.listdir_attr(remote_dir):
        remote_path = remote_dir + "/" + entry.filename
        local_path = os.path.join(local_dir, entry.filename)
        if S_ISDIR(entry.st_mode):
            download_dir(sftp, remote_path, local_path)
        else:
            print(f"Downloading {remote_path} to {local_path}...")
            sftp.get(remote_path, local_path)

def sync(host, user, password, remote_root, local_root):
    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=30)
        sftp = ssh.open_sftp()
        print("Syncing /root/ultimate_engine...")
        download_dir(sftp, remote_root, local_root)
        print("Sync complete!")
        sftp.close()
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync("45.32.255.155", "root", "6{tJs[Dhe,jv3@_G", "/root/ultimate_engine", "c:\\Users\\ASUS\\ultimate_engine")
