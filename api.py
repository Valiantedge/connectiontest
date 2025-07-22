# cloud_server_api.py - Runs on your cloud server

from flask import Flask, request, jsonify # pip install Flask
import uuid
import logging
import queue # For a simple in-memory queue, replace with Redis/DB for production

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Simple In-Memory Queue (Replace with persistent storage like Redis, DB for production) ---
command_queue = {} # Stores commands {agent_id: [command_payload1, command_payload2]}
command_results = {} # Stores results {correlation_id: result_payload}

# --- API Endpoint for Agents to Poll for Commands ---
@app.route("/api/commands", methods=["GET"])
def get_commands_for_agent():
    agent_id = request.args.get("agent_id")
    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    # Retrieve commands for this agent
    commands_to_send = command_queue.get(agent_id, [])
    command_queue[agent_id] = [] # Clear commands after sending

    logging.info(f"Agent '{agent_id}' polled. Sending {len(commands_to_send)} commands.")
    return jsonify(commands_to_send)

# --- API Endpoint for Agents to Report Results ---
@app.route("/api/commands/results", methods=["POST"])
def receive_command_results():
    result_payload = request.json
    correlation_id = result_payload.get("correlation_id")
    if not correlation_id:
        return jsonify({"error": "correlation_id is required"}), 400

    command_results[correlation_id] = result_payload
    logging.info(f"Received results for correlation_id: {correlation_id}")
    return jsonify({"status": "success"})

# --- Endpoint to Queue a Command for the Agent ---
@app.route("/api/queue_command", methods=["POST"])
def queue_command():
    data = request.json
    target_agent_id = data.get("agent_id")
    target_host = data.get("target_host")
    target_type = data.get("target_type")
    command_to_execute = data.get("command")

    if not all([target_agent_id, target_host, target_type, command_to_execute]):
        return jsonify({"error": "Missing required fields"}), 400

    correlation_id = str(uuid.uuid4())
    command_payload = {
        "correlation_id": correlation_id,
        "target_host": target_host,
        "target_type": target_type,
        "command": command_to_execute
    }

    if target_agent_id not in command_queue:
        command_queue[target_agent_id] = []
    command_queue[target_agent_id].append(command_payload)

    logging.info(f"Queued command for agent '{target_agent_id}' (Correlation ID: {correlation_id})")
    return jsonify({"status": "queued", "correlation_id": correlation_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) # Ensure port 5000 is open in cloud server firewall
