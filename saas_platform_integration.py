"""
SaaS Platform Integration Example
How your SaaS platform connects to user's VPN-connected agent for deployments
"""

import requests
import json
import time
from typing import Dict, List, Optional

class SaaSPlatformClient:
    """
    Client for connecting to user's deployment agent
    This runs on your SaaS platform (AWS/Cloud)
    """
    
    def __init__(self, user_agent_url: str):
        """
        Initialize with user's agent URL
        Example: http://user_laptop_ip:5001
        """
        self.agent_url = user_agent_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_connection(self) -> Dict:
        """Test if user's agent is accessible"""
        try:
            response = self.session.get(f"{self.agent_url}/health")
            return {
                'success': True,
                'status': response.json(),
                'agent_accessible': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent_accessible': False
            }
    
    def test_ssh_to_private_server(self, server_config: Dict) -> Dict:
        """
        Test SSH connection to user's private server through their VPN
        
        Args:
            server_config: {
                'host': '192.168.1.100',  # Private server IP
                'port': 22,
                'username': 'admin',
                'password': 'server_password',
                'commands': ['hostname', 'uptime', 'docker ps']
            }
        """
        try:
            response = self.session.post(
                f"{self.agent_url}/ssh-test",
                json=server_config
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def deploy_ansible(self, playbook: str, inventory: str, variables: Dict = None) -> Dict:
        """
        Deploy Ansible playbook through user's VPN connection
        
        Args:
            playbook: Ansible playbook YAML content
            inventory: Inventory file content
            variables: Extra variables for the playbook
        """
        deployment_data = {
            'type': 'ansible',
            'playbook': playbook,
            'inventory': inventory,
            'variables': variables or {}
        }
        
        try:
            response = self.session.post(
                f"{self.agent_url}/deploy",
                json=deployment_data
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def deploy_terraform(self, tf_config: str, command: str = 'apply') -> Dict:
        """
        Deploy Terraform configuration through user's VPN
        
        Args:
            tf_config: Terraform configuration (.tf file content)
            command: terraform command (plan, apply, destroy)
        """
        deployment_data = {
            'type': 'terraform',
            'config': tf_config,
            'command': command
        }
        
        try:
            response = self.session.post(
                f"{self.agent_url}/deploy", 
                json=deployment_data
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute_shell_script(self, script: str, shell: str = 'powershell') -> Dict:
        """
        Execute shell script through user's VPN connection
        
        Args:
            script: Shell script content
            shell: Shell type (powershell, cmd, bash)
        """
        deployment_data = {
            'type': 'shell',
            'script': script,
            'shell': shell
        }
        
        try:
            response = self.session.post(
                f"{self.agent_url}/deploy",
                json=deployment_data
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Example usage in your SaaS platform
def deploy_user_application(user_id: str, deployment_config: Dict):
    """
    Example: How your SaaS platform deploys to user's private infrastructure
    """
    
    # Get user's agent URL from your database
    user_agent_url = get_user_agent_url(user_id)  # Your function
    
    if not user_agent_url:
        return {'error': 'User agent not configured'}
    
    # Initialize client
    client = SaaSPlatformClient(user_agent_url)
    
    # Test connectivity
    connection_test = client.test_connection()
    if not connection_test['success']:
        return {
            'error': 'Cannot connect to user agent. Please ensure VPN is connected and agent is running.',
            'details': connection_test
        }
    
    # Test SSH to target servers
    for server in deployment_config.get('servers', []):
        ssh_test = client.test_ssh_to_private_server(server)
        if not ssh_test['success']:
            return {
                'error': f'Cannot connect to server {server["host"]}',
                'details': ssh_test
            }
    
    # Proceed with deployment
    deployment_type = deployment_config.get('type')
    
    if deployment_type == 'ansible':
        result = client.deploy_ansible(
            playbook=deployment_config['playbook'],
            inventory=deployment_config['inventory'],
            variables=deployment_config.get('variables', {})
        )
    elif deployment_type == 'terraform':
        result = client.deploy_terraform(
            tf_config=deployment_config['terraform_config'],
            command=deployment_config.get('command', 'apply')
        )
    elif deployment_type == 'shell':
        result = client.execute_shell_script(
            script=deployment_config['script'],
            shell=deployment_config.get('shell', 'powershell')
        )
    else:
        return {'error': 'Unknown deployment type'}
    
    # Log the deployment result
    log_deployment(user_id, deployment_config, result)  # Your logging function
    
    return result

def get_user_agent_url(user_id: str) -> Optional[str]:
    """
    Get user's agent URL from your database
    Replace this with your actual database lookup
    """
    # Example implementation
    user_agents = {
        'user123': 'http://10.0.1.50:5001',  # User's laptop IP
        'user456': 'http://192.168.1.100:5001'
    }
    return user_agents.get(user_id)

def log_deployment(user_id: str, config: Dict, result: Dict):
    """Log deployment results to your system"""
    print(f"Deployment for {user_id}: {'SUCCESS' if result.get('success') else 'FAILED'}")
    # Add your logging logic here

# Example deployment configurations
EXAMPLE_ANSIBLE_DEPLOYMENT = {
    'type': 'ansible',
    'servers': [{
        'host': '192.168.1.100',
        'port': 22,
        'username': 'admin',
        'password': 'server_password',
        'commands': ['docker --version']
    }],
    'playbook': '''
---
- hosts: all
  tasks:
    - name: Install Docker
      apt:
        name: docker.io
        state: present
    - name: Start Docker service
      service:
        name: docker
        state: started
        enabled: yes
''',
    'inventory': '''
[webservers]
192.168.1.100 ansible_user=admin ansible_ssh_pass=server_password
'''
}

EXAMPLE_TERRAFORM_DEPLOYMENT = {
    'type': 'terraform',
    'servers': [{
        'host': '192.168.1.100',
        'port': 22,
        'username': 'admin', 
        'password': 'server_password'
    }],
    'terraform_config': '''
resource "local_file" "test" {
  content  = "Hello from SaaS platform via VPN!"
  filename = "/tmp/saas-deployment.txt"
}
''',
    'command': 'apply'
}

EXAMPLE_SHELL_DEPLOYMENT = {
    'type': 'shell',
    'script': '''
# Deploy application via SSH
ssh admin@192.168.1.100 "
    cd /opt/myapp
    git pull origin main
    docker-compose down
    docker-compose up -d
    echo 'Deployment complete'
"
''',
    'shell': 'bash'
}

if __name__ == "__main__":
    # Test deployment
    result = deploy_user_application('user123', EXAMPLE_SHELL_DEPLOYMENT)
    print(json.dumps(result, indent=2))
