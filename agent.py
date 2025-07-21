import uuid
import sys
import json
import paramiko
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)

import uuid

CORS(app)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route("/ssh-test", methods=["POST"])
def ssh_test():
    data = request.json
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=data["host"],
            port=data.get("port", 22),
            username=data["username"],
            password=data["password"],
            timeout=10
        )

        results = []
        for cmd in data.get("commands", ["hostname", "uptime"]):
            stdin, stdout, stderr = client.exec_command(cmd)
            results.append({
                "command": cmd,
                "output": stdout.read().decode(),
                "error": stderr.read().decode()
            })

        client.close()
        return jsonify({"success": True, "results": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/deploy", methods=["POST"])
def deploy():
    data = request.json
    deploy_type = data.get("type")  # ansible, terraform, shell
    test_id = str(uuid.uuid4())

    try:
        if deploy_type == "shell":
            result = subprocess.run(data["script"], shell=True, capture_output=True, text=True)
            response = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "test_id": test_id
            }
            print("Deploy response:", response)
            return jsonify(response)
        else:
            response = {
                "success": False,
                "error": f"Unknown deploy type: {deploy_type}",
                "test_id": test_id
            }
            print("Deploy response:", response)
            return jsonify(response)
    except Exception as e:
        response = {"success": False, "error": str(e), "test_id": test_id}
        print("Deploy response:", response)
        return jsonify(response)

if __name__ == "__main__":
    print("SaaS Deployment Agent starting on port 5001...")
    print("Your SaaS platform can now connect to this machine for deployments")
    app.run(host="0.0.0.0", port=5001, debug=False)