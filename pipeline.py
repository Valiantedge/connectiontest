# orchestrator.py - Runs on your cloud server

import requests # pip install requests
import time
import json
import logging

# --- Configuration ---
CLOUD_SERVER_API_URL = "http://localhost:5000" # Point to your Flask API if running locally, or public IP if accessed externally
AGENT_ID = "onprem-windows-bridge-001" # Target agent ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Function to send a command to the agent via the API ---
def send_command_to_agent(target_host, target_type, command_str):
    payload = {
        "agent_id": AGENT_ID,
        "target_host": target_host,
        "target_type": target_type,
        "command": command_str
    }
    try:
        response = requests.post(f"{CLOUD_SERVER_API_URL}/api/queue_command", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("correlation_id")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending command: {e}")
        return None

# --- Function to check for command results ---
def get_command_results(correlation_id, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        # In a real system, you'd have a database or Redis to store results
        # and an API endpoint to query them, or the agent pushes to a different endpoint.
        # For this simple example, we'll assume the Flask API stores results in memory.
        results = requests.get(f"{CLOUD_SERVER_API_URL}/api/commands/results", params={"correlation_id": correlation_id})
        if correlation_id in app.command_results: # Accessing global Flask variable - not ideal for production
            return app.command_results.pop(correlation_id) # Retrieve and clear
        time.sleep(5) # Wait before checking again
    return {"status": "timeout", "message": "Command timed out"}

# --- Example Usage ---
if __name__ == "__main__":
    # --- Example 1: Run a shell script on a Linux server via the Windows agent ---
    linux_target_ip = "192.168.1.100" # Replace with actual
    shell_script_content = "uptime; hostname"
    correlation_id_linux = send_command_to_agent(linux_target_ip, "linux", shell_script_content)

    if correlation_id_linux:
        logging.info(f"Queued shell script for {linux_target_ip} with ID: {correlation_id_linux}")
        results = get_command_results(correlation_id_linux)
        logging.info(f"Results for Linux script ({correlation_id_linux}): {json.dumps(results, indent=2)}")

    # --- Example 2: Run an Ansible playbook (hypothetically) via the Windows agent ---
    # Note: Running Ansible playbooks via this "command string" method
    # is more complex. Ansible expects an SSH connection, not just a shell command.
    # You'd typically need Ansible *within* a WSL environment on the Windows agent,
    # and the agent script would call `wsl ansible-playbook ...` locally.

    # The more practical way: Ansible on Cloud server uses ProxyCommand to tunnel via agent's SSH/WinRM
    # This requires the cloud server's Ansible to have an inventory configured with the ProxyCommand
    # and the agent to accept raw SSH connections for tunneling.

    # For instance, if you want Ansible on the cloud to run against a Linux server:
    # 1. On Cloud: Have your playbook and inventory.ini:
    #    # inventory.ini
    #    [private_servers]
    #    my_onprem_linux_server ansible_host=192.
