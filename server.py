from flask import Flask, request, jsonify
import threading
import time
import subprocess
import uuid

app = Flask(__name__)
agents = {}
tasks = {}
results = {}

@app.route('/api/register', methods=['POST'])
def register_agent():
    agent_id = str(uuid.uuid4())
    agents[agent_id] = {'status': 'active', 'last_seen': time.time()}
    return jsonify({'agent_id': agent_id})

@app.route('/api/tasks/<agent_id>', methods=['GET'])
def get_task(agent_id):
    task = tasks.get(agent_id)  # ✅ this keeps the task until agent confirms
    if task:
        return jsonify(task)
    return jsonify({'task': None})

@app.route('/api/results', methods=['POST'])
def receive_result():
    data = request.json
    agent_id = data['agent_id']
    task_id = data['task_id']
    result = data['result']
    results[(agent_id, task_id)] = result
    print(f"[SERVER] Result received for agent {agent_id}, task {task_id}: {result}")
    return jsonify({'status': 'received'})

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    data = request.json
    agent_id = data['agent_id']
    task = data['task']
    tasks[agent_id] = task
    print(f"[SERVER] Task added for agent {agent_id}: {task}")
    return jsonify({'status': 'task added'})

@app.route('/api/deploy/run', methods=['POST'])
def run_deploy_script():
    """Run ./deploy.sh locally on server"""
    try:
        print("[SERVER] Running './deploy.sh deploy' ...")
        result = subprocess.run(["bash", "./deploy.sh"], capture_output=True, text=True)

        return jsonify({
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def cleanup_inactive_agents():
    while True:
        now = time.time()
        for agent_id in list(agents):
            if now - agents[agent_id]['last_seen'] > 300:  # 5 minutes timeout
                print(f"[SERVER] Agent {agent_id} removed due to inactivity")
                del agents[agent_id]
        time.sleep(60)

# Start agent cleanup thread
threading.Thread(target=cleanup_inactive_agents, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
