"""
SaaS SSH Connection Testing API
Flask API endpoint for your SaaS platform
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import json
import threading
import uuid
from datetime import datetime
from saas_ssh_tester import SaaSSSHConnectionTester
from saas_deployment_service import SaaSDeploymentTester
import os

import os
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Store test results temporarily (use Redis/Database in production)
test_results = {}
deployment_results = {}


# Serve index.html at root
@app.route("/")
def root():
    return send_from_directory(".", "index.html")

# Serve download page
@app.route("/download")
def download_page():
    return send_from_directory(".", "download_page.html")

# Serve test connection UI
@app.route("/test")
def test_page():
    return send_from_directory(".", "saas_web_interface.html")

@app.route('/api/deployment/test', methods=['POST'])
def test_deployment():
    """
    API endpoint to test deployment connectivity
    
    Expected JSON payload:
    {
        "target_server": {
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin", 
            "password": "password",
            "auth_method": "password"
        },
        "tunnel": {
            "enabled": true,
            "host": "user_laptop_ip",
            "username": "user_laptop_username",
            "password": "user_laptop_password"
        },
        "deployment": {
            "type": "shell|ansible|terraform",
            "script": "shell script content",
            "playbook": {...},
            "config": {...}
        }
    }
    """
    try:
        config = request.get_json()
        
        # Add test ID
        test_id = str(uuid.uuid4())
        config['test_id'] = test_id
        
        # Start deployment test in background
        def run_deployment_test():
            tester = SaaSDeploymentTester()
            result = tester.test_deployment_connectivity(config)

            if result is None:
                result = {
                    'success': False,
                    'error': 'No result returned from deployment test'
                }

            result['test_id'] = test_id
            if 'saas_type' in config:
                result['saas_type'] = config['saas_type']

            print(f"[{test_id}] Deployment Test Result:", result)


        
        thread = threading.Thread(target=run_deployment_test, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': 'Deployment test started',
            'status_url': f'/api/deployment/test/{test_id}'
        }), 202
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/deployment/test/<test_id>', methods=['GET'])
def get_deployment_result(test_id):
    """Get the result of a specific deployment test"""
    
    if test_id not in deployment_results:
        return jsonify({
            'success': False,
            'error': 'Test not found or still running',
            'status': 'running'
        }), 202
    
    result = deployment_results[test_id]
    return jsonify(result)

@app.route('/api/deployment/test/<test_id>', methods=['DELETE'])
def delete_deployment_result(test_id):
    """Delete a deployment test result"""
    if test_id in deployment_results:
        del deployment_results[test_id]
    
    return jsonify({'success': True, 'message': 'Deployment test result deleted'})

@app.route('/api/ssh/test', methods=['POST'])
def test_ssh_connection():
    """
    API endpoint to test SSH connection
    
    Expected JSON payload:
    {
        "target_server": {
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin", 
            "password": "password",
            "auth_method": "password"
        },
        "tunnel": {
            "enabled": true,
            "host": "user_laptop_ip",
            "username": "user_laptop_username",
            "password": "user_laptop_password"
        },
        "commands": ["hostname", "uptime"],
        "user_id": "user123"
    }
    """
    try:
        config = request.get_json()
        # Add test ID
        test_id = str(uuid.uuid4())
        config['test_id'] = test_id
        # Start deployment test in background
        def run_deployment_test():
            tester = SaaSDeploymentTester()
            result = tester.test_deployment_connectivity(config)
            if result is None:
                result = {
                    'success': False,
                    'error': 'No result returned from deployment test'
                }
            result['test_id'] = test_id
            if 'saas_type' in config:
                result['saas_type'] = config['saas_type']
            print(f"[{test_id}] Deployment Test Result:", result)
            # ✅ Ensure test_id is always injected into the result
            # Optional debug log to confirm what’s being stored
            print(f"[DEBUG] Final deployment result for test_id={test_id}: {result}")
            # Store result in shared dictionary
            deployment_results[test_id] = result
        thread = threading.Thread(target=run_deployment_test, daemon=True)
        thread.start()
        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': 'SSH connection test started',
            'status_url': f'/api/ssh/test/{test_id}'
        }), 202
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
def delete_test_result(test_id):
    """Delete a test result"""
    if test_id in test_results:
        del test_results[test_id]
    
    return jsonify({'success': True, 'message': 'Test result deleted'})

@app.route('/api/tests', methods=['GET'])
def list_all_tests():
    """List all test results"""
    return jsonify({
        'ssh_tests': list(test_results.keys()),
        'deployment_tests': list(deployment_results.keys()),
        'total_ssh_tests': len(test_results),
        'total_deployment_tests': len(deployment_results)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SSH Connection Testing API',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
