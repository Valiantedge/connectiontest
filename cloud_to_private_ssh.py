import subprocess

# Replace these with your actual values
private_server_ip = "192.168.1.100"
private_server_user = "admin"
windows_agent_user = "winuser"
windows_agent_public_ip = "AGENT_PUBLIC_IP"
remote_command = "whoami"  # The command you want to run on the private server

# Build the SSH command with ProxyJump
ssh_cmd = [
    "ssh",
    "-J", f"{windows_agent_user}@{windows_agent_public_ip}",
    f"{private_server_user}@{private_server_ip}",
    remote_command
]

result = subprocess.run(ssh_cmd, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
