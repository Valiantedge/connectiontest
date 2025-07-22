import subprocess

# Path to your Ansible playbook and inventory
playbook_path = "install_apache.yml"
inventory_path = "inventory"

# Run ansible-playbook with ProxyJump (jump host)
command = [
    "ansible-playbook",
    "-i", inventory_path,
    playbook_path
]

result = subprocess.run(command, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
