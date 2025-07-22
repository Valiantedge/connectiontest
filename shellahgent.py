import os
import time
import uuid
import requests
import subprocess
from flask import Flask, jsonify

# Constants
AGENT_ID_FILE = "agent_id.txt"
TASK_API_URL_TEMPLATE = "http://13.58.212.239:5000/api/tasks/{agent_id}"
RESULTS_API_URL = "http://13.58.212.239:5000/api/results"
REGISTER_API_URL = "http://13.58.212.239:5000/api/register"


# Generate or read agent ID
if os.path.exists(AGENT_ID_FILE):
    with open(AGENT_ID_FILE, "r") as f:
        AGENT_ID = f.read().strip()
else:
    AGENT_ID = str(uuid.uuid4())
    with open(AGENT_ID_FILE, "w") as f:
        f.write(AGENT_ID)

print(f"[AGENT] Agent ID: {AGENT_ID}")

# Flask App
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK", "agent_id": AGENT_ID})

@app.route('/run-deploy', methods=['POST'])
def run_deploy():
    print("[AGENT] Running ./deploy.sh ")
    try:
        result = subprocess.run(["./deploy.sh"], capture_output=True, text=True)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Polling loop to fetch and execute tasks
def poll_for_tasks():
    while True:
        try:
            print("[AGENT] Polling for tasks...")
            response = requests.get(TASK_API_URL_TEMPLATE.format(agent_id=AGENT_ID), timeout=10)

            if response.status_code == 200:
                tasks = response.json().get("tasks", [])
                if not tasks:
                    print("[AGENT] No tasks received.")
                for task in tasks:
                    print(f"[AGENT] Received task: {task}")
                    task_type = task.get("type")
                    task_id = task.get("task_id")

                    if task_type == "shell":
                        shell_data = task["data"]
                        shell_command = shell_data.get("script")  # e.g., ./deploy.sh deploy
                        print(f"[AGENT][SHELL] Running shell command: {shell_command}")
                        try:
                            result = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
                            result_payload = {
                                "agent_id": AGENT_ID,
                                "task_id": task_id,
                                "success": result.returncode == 0,
                                "output": result.stdout,
                                "error": result.stderr
                            }
                        except Exception as e:
                            result_payload = {
                                "agent_id": AGENT_ID,
                                "task_id": task_id,
                                "success": False,
                                "error": str(e)
                            }

                        # Send result
                        try:
                            resp = requests.post(RESULTS_API_URL, json=result_payload, timeout=10)
                            print(f"[AGENT] Sent shell result for task {task_id}: {resp.status_code} {resp.text}")
                        except Exception as e:
                            print(f"[AGENT][ERROR] Failed to send shell result: {e}")

                    else:
                        print(f"[AGENT] Unknown task type: {task_type}")
            else:
                print(f"[AGENT][ERROR] Bad response from server: {response.status_code} {response.text}")
        except Exception as e:
            print(f"[AGENT][ERROR] Exception while polling tasks: {e}")
        time.sleep(10)  # Poll interval

# Run agent
if __name__ == '__main__':
    # Run polling in background
    import threading
    polling_thread = threading.Thread(target=poll_for_tasks, daemon=True)
    polling_thread.start()

    # Run Flask app (local access only)
    app.run(host="0.0.0.0", port=8000)
