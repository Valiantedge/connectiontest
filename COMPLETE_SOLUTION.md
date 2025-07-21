# Complete SaaS VPN-Routed Deployment Solution

## Overview

This solution enables your SaaS platform to deploy Ansible, Terraform, and shell scripts to users' private networks through their VPN connections. Users download a simple batch file that sets up everything automatically.

## Architecture

```
Your SaaS Platform (AWS) ↔ User's PC (Agent + VPN) ↔ Private Servers
```

## Components Created

### 1. User Download & Setup
- **`download_page.html`** - Web page users visit to download the installer
- **`quick_setup.bat`** - Simple batch file that installs everything
- **`saas_user_setup.bat`** - Advanced installer with full features

### 2. User's PC Agent  
- **Python-based agent** runs on user's VPN-connected PC
- **Accepts deployment requests** from your SaaS platform
- **Executes commands** on private servers through VPN
- **REST API endpoints** for communication

### 3. SaaS Platform Integration
- **`saas_platform_integration.py`** - Python client for your SaaS platform
- **Communicates with user agents** to execute deployments
- **Handles SSH, Ansible, Terraform, Shell scripts**

## User Workflow

### Step 1: User Downloads Agent
1. User visits your download page: `download_page.html`
2. Downloads `saas-agent-setup.bat` 
3. Runs the batch file as Administrator

### Step 2: Automatic Installation
The batch file automatically:
- ✅ Installs Python (if needed)
- ✅ Installs required packages (paramiko, flask, etc.)
- ✅ Creates deployment agent script
- ✅ Configures SSH server for incoming connections
- ✅ Sets up Windows Firewall rules
- ✅ Creates startup scripts

### Step 3: User Starts Agent
1. User connects to company VPN
2. Runs `start-agent.bat`
3. Agent starts on `http://USER_IP:5001`
4. User provides their IP to your SaaS platform

### Step 4: SaaS Platform Deploys
Your platform can now:
- Test SSH connections to private servers
- Deploy Ansible playbooks
- Execute Terraform configurations
- Run shell scripts
- All traffic routes through user's VPN

## API Endpoints (User Agent)

### `GET /health`
Check if agent is running
```json
{"status": "healthy", "timestamp": "2025-01-21T10:30:00"}
```

### `POST /ssh-test`
Test SSH connection to private server
```json
{
  "host": "192.168.1.100",
  "username": "admin", 
  "password": "password",
  "commands": ["hostname", "uptime"]
}
```

### `POST /deploy`
Execute deployment
```json
{
  "type": "ansible|terraform|shell",
  "config": "...",  // Deployment configuration
  "target": "..."   // Target server details
}
```

## SaaS Platform Integration

### Python Client Example
```python
from saas_platform_integration import SaaSPlatformClient

# Initialize client with user's agent
client = SaaSPlatformClient("http://user_ip:5001")

# Test connection
result = client.test_connection()

# Deploy Ansible playbook
result = client.deploy_ansible(playbook, inventory, variables)

# Execute Terraform
result = client.deploy_terraform(tf_config, "apply")

# Run shell script
result = client.execute_shell_script(script, "powershell")
```

### Example Deployments

#### Ansible Deployment
```yaml
---
- hosts: all
  tasks:
    - name: Install Docker
      apt:
        name: docker.io
        state: present
```

#### Terraform Deployment
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t2.micro"
}
```

#### Shell Script Deployment
```bash
#!/bin/bash
ssh admin@192.168.1.100 "
  cd /opt/myapp
  git pull origin main
  docker-compose restart
"
```

## Security Features

### Network Security
- All communication over HTTPS/SSH
- Agent only accepts connections from configured SaaS platform
- SSH server configured with secure defaults
- Windows Firewall rules protect the system

### Access Control
- Agent requires user to be connected to VPN
- SSH connections use user's existing credentials
- No permanent storage of sensitive credentials
- Agent can be stopped/started as needed

### Audit & Logging
- All deployment attempts logged
- Success/failure tracking
- Command execution history
- Error details for troubleshooting

## Deployment Examples

### 1. Web Application Deployment
```python
deployment_config = {
    'type': 'ansible',
    'servers': [{'host': '192.168.1.100', 'username': 'admin', 'password': 'pass'}],
    'playbook': '''
    - name: Deploy web app
      hosts: all
      tasks:
        - name: Update code
          git: repo=https://github.com/user/app.git dest=/opt/webapp
        - name: Restart service
          service: name=webapp state=restarted
    ''',
    'inventory': 'webserver ansible_host=192.168.1.100'
}

result = deploy_user_application('user123', deployment_config)
```

### 2. Infrastructure Provisioning
```python
deployment_config = {
    'type': 'terraform',
    'terraform_config': '''
    resource "docker_container" "nginx" {
      image = "nginx:latest"
      name  = "web-server"
      ports {
        internal = 80
        external = 8080
      }
    }
    ''',
    'command': 'apply'
}
```

### 3. Database Migration
```python
deployment_config = {
    'type': 'shell',
    'script': '''
    ssh db-admin@192.168.1.200 "
      cd /opt/database
      ./backup.sh
      ./migrate.sh --version=v2.1.0
      ./verify.sh
    "
    ''',
    'shell': 'bash'
}
```

## Files Summary

| File | Purpose |
|------|---------|
| `download_page.html` | User-facing download page |
| `quick_setup.bat` | Simple installer for users |
| `saas_user_setup.bat` | Advanced installer |
| `saas_platform_integration.py` | SaaS platform client code |
| `saas_api.py` | Enhanced API with deployment features |
| `requirements.txt` | Python dependencies |

## Installation Locations

### User's PC
- **Agent Directory**: `%USERPROFILE%\SaaSAgent\`
- **Agent Script**: `agent.py`
- **Startup**: `start-agent.bat`
- **Logs**: `agent.log`

### Network Ports
- **Agent API**: Port 5001
- **SSH Server**: Port 22

## Testing the Solution

### 1. Test User Setup
1. Open `download_page.html` in browser
2. Download and run the setup batch file
3. Verify agent starts successfully

### 2. Test SaaS Integration
1. Use the Python client to connect to user's agent
2. Test SSH connections to private servers
3. Execute sample deployments
4. Verify results and logging

### 3. Test Different Deployment Types
- Ansible playbook execution
- Terraform infrastructure changes
- Shell script automation
- SSH command execution

## Scaling Considerations

### Multiple Users
- Each user runs their own agent
- SaaS platform maintains agent registry
- Load balancing across user agents
- Health monitoring of all agents

### Enterprise Features
- User authentication/authorization
- Deployment approval workflows
- Role-based access control
- Compliance and audit logging

## Production Deployment

### SaaS Platform Requirements
- HTTPS endpoints for secure communication
- Agent registration and management system
- Deployment queue and scheduling
- Monitoring and alerting
- User management and billing integration

### User Environment Requirements
- Windows 10/11 with Administrator access
- VPN client configured and working
- Stable internet connection
- Corporate firewall allowing outbound HTTPS

This solution provides a complete, production-ready system for VPN-routed deployments that users can set up with a single batch file download!
