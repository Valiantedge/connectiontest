# windows_agent.py - Runs on the Windows machine

import subprocess
import json
import os
import sys
import requests # pip install requests
import time
import logging

# --- Agent Configuration ---
# Cloud server API endpoint for receiving commands
CLOUD_SERVER_API_URL = "http://your.cloud.server.ip.or.hostname:5000/api/commands" # Replace with your cloud server's actual URL
AGENT_ID = "onprem-windows-bridge-001" # Unique ID for this agent
POLLING_INTERVAL_SECONDS = 5 # How often the agent checks for new commands
LOG_FILE = "agent_log.txt"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Function to securely get credentials (replace with your secure method) ---
def get_credentials(target_type, target_host):
    # In a real scenario, use Windows Credential Manager, a secure vault,
    # or environment variables for SSH private key paths and WinRM passwords.
    # DO NOT hardcode passwords here.
    if target_type == "linux":
        # Example: Path to SSH private key accessible by the agent
        return {
            "username": "remote_linux_username", # Replace
            "ssh_key_path": "C:\\Users\\AgentUser\\.ssh\\id_rsa" # Replace with actual path
        }
    elif target_type == "windows":
        return {
            "username": "remote_windows_username", # Replace
            "password": "your_winrm_password" # Replace with secure retrieval
        }
    return None

# --- Function to execute commands ---
def execute_command_on_private_server(command_payload):
    target_host = command_payload.get("target_host")
    target_type = command_payload.get("target_type")
    command_to_execute = command_payload.get("command")
    correlation_id = command_payload.get("correlation_id", "N/A")

    if not target_host or not target_type or not command_to_execute:
        logging.error(f"[{correlation_id}] Invalid command payload: {command_payload}")
        return {"status": "error", "message": "Invalid command payload", "correlation_id": correlation_id}

    creds = get_credentials(target_type, target_host)
    if not creds:
        logging.error(f"[{correlation_id}] No credentials found for target type: {target_type} on {target_host}")
        return {"status": "error", "message": "Credentials not found", "correlation_id": correlation_id}

    result = {"status": "success", "stdout": "", "stderr": "", "return_code": 0, "correlation_id": correlation_id}

    try:
        if target_type == "linux":
            # Using ssh.exe which should be available on Windows (e.g., via WSL or built-in OpenSSH)
            # You might need to adjust the path or use 'plink.exe' if PuTTY is preferred.
            ssh_cmd = ["ssh.exe", "-i", creds["ssh_key_path"], f"{creds['username']}@{target_host}", command_to_execute]
            process = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["return_code"] = process.returncode
        elif target_type == "windows":
            # Using PowerShell to execute via WinRM
            # This assumes WinRM is configured on the target Windows server.
            # WARNING: Passing passwords directly to powershell.exe is INSECURE.
            # Use secure methods for real deployments (e.g., Invoke-Command with saved credentials).
            powershell_script = f"""
            $cred = New-Object System.Management.Automation.PSCredential ("{creds['username']}", (ConvertTo-SecureString "{creds['password']}" -AsPlainText -Force))
            Invoke-Command -ComputerName {target_host} -Credential $cred -ScriptBlock {{ {command_to_execute} }}
            """
            # Use shell=True with extreme caution for security
            process = subprocess.run(["powershell.exe", "-Command", powershell_script], capture_output=True, text=True, check=True, shell=True)
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["return_code"] = process.returncode
        else:
            raise ValueError(f"Unsupported target type: {target_type}")

        logging.info(f"[{correlation_id}] Command executed on {target_host}: {command_to_execute}")
        logging.info(f"[{correlation_id}] Stdout: {result['stdout'].strip()}")
        logging.info(f"[{correlation_id}] Stderr: {result['stderr'].strip()}")

    except subprocess.CalledProcessError as e:
        logging.error(f"[{correlation_id}] Command execution failed on {target_host}: {e}")
        logging.error(f"[{correlation_id}] Stderr: {e.stderr.strip()}")
        result["status"] = "failed"
        result["stdout"] = e.stdout
        result["stderr"] = e.stderr
        result["return_code"] = e.returncode
    except FileNotFoundError:
        logging.error(f"[{correlation_id}] SSH or PowerShell executable not found on agent machine.")
        result["status"] = "error"
        result["message"] = "Remote execution tool (SSH/PowerShell) not found."
    except Exception as e:
        logging.error(f"[{correlation_id}] Unexpected error during command execution: {e}", exc_info=True)
        result["status"] = "error"
        result["message"] = str(e)
    return result

# --- Agent's main loop to poll for commands ---
def start_agent():
    logging.info(f"Windows Agent '{AGENT_ID}' started. Polling for commands from {CLOUD_SERVER_API_URL}")
    while True:
        try:
            # Poll the cloud server for new commands
            response = requests.get(CLOUD_SERVER_API_URL, params={"agent_id": AGENT_ID}, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            commands = response.json()
            if commands and isinstance(commands, list):
                for command_payload in commands:
                    logging.info(f"Received command: {command_payload.get('correlation_id', 'N/A')}")
                    execution_result = execute_command_on_private_server(command_payload)

                    # Send results back to the cloud server (could be a different API endpoint)
                    requests.post(f"{CLOUD_SERVER_API_URL}/results", json=execution_result)
            else:
                logging.debug("No commands received.")

        except requests.exceptions.Timeout:
            logging.warning("Cloud server API request timed out.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with cloud server API: {e}")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response from cloud server: {response.text}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in agent loop: {e}", exc_info=True)

        time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    start_agent()

