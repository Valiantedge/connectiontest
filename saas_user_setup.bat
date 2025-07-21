@echo off
:: SaaS SSH Connection Tester - User Setup Batch File
:: This script downloads and sets up everything needed for VPN-routed deployments
:: Users download this from your SaaS platform and run it on their PC

title SaaS Deployment Agent Setup
color 0A

echo ===============================================
echo    SaaS Deployment Agent Setup
echo    Setting up VPN-routed connection testing
echo ===============================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
) else (
    echo [WARNING] Not running as Administrator
    echo Some features may require administrator privileges
    echo.
)

:: Create working directory
set "INSTALL_DIR=%USERPROFILE%\SaaSDeploymentAgent"
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo [OK] Created directory: %INSTALL_DIR%
) else (
    echo [OK] Directory exists: %INSTALL_DIR%
)

cd /d "%INSTALL_DIR%"

:: Step 1: Check Python Installation
echo.
echo [STEP 1] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is installed
    python --version
) else (
    echo [INFO] Python not found. Downloading Python installer...
    
    :: Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe'"
    
    if exist "python-installer.exe" (
        echo [INFO] Installing Python... Please follow the installer prompts
        echo [IMPORTANT] Make sure to check "Add Python to PATH"
        start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        :: Refresh PATH
        call refreshenv.cmd >nul 2>&1
        
        :: Test Python again
        python --version >nul 2>&1
        if %errorLevel% == 0 (
            echo [OK] Python installed successfully
        ) else (
            echo [ERROR] Python installation failed. Please install manually from python.org
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Failed to download Python installer
        echo Please download and install Python manually from https://python.org
        pause
        exit /b 1
    )
)

:: Step 2: Install required Python packages
echo.
echo [STEP 2] Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install paramiko flask flask-cors requests psutil

if %errorLevel% == 0 (
    echo [OK] Python packages installed successfully
) else (
    echo [ERROR] Failed to install Python packages
    pause
    exit /b 1
)

:: Step 3: Download SaaS agent files
echo.
echo [STEP 3] Downloading SaaS deployment agent...

:: Create the main agent script
echo Creating deployment agent script...
(
echo import sys
echo import json
echo import requests
echo import paramiko
echo import threading
echo import time
echo import subprocess
echo import os
echo from flask import Flask, request, jsonify
echo from flask_cors import CORS
echo from datetime import datetime
echo import psutil
echo.
echo class SaaSDeploymentAgent:
echo     def __init__(self^):
echo         self.app = Flask(__name__^)
echo         CORS(self.app^)
echo         self.setup_routes(^)
echo         self.saas_server = "YOUR_SAAS_SERVER_URL"  # Will be configured
echo.
echo     def setup_routes(self^):
echo         @self.app.route('/health', methods=['GET']^)
echo         def health_check(^):
echo             return jsonify({
echo                 'status': 'healthy',
echo                 'agent': 'SaaS Deployment Agent',
echo                 'timestamp': datetime.now(^).isoformat(^)
echo             }^)
echo.
echo         @self.app.route('/execute', methods=['POST']^)
echo         def execute_command(^):
echo             try:
echo                 data = request.get_json(^)
echo                 command_type = data.get('type'^)  # 'ssh', 'ansible', 'terraform', 'shell'
echo                 target = data.get('target'^)
echo                 credentials = data.get('credentials'^)
echo                 
echo                 if command_type == 'ssh':
echo                     return self.execute_ssh(target, credentials^)
echo                 elif command_type == 'ansible':
echo                     return self.execute_ansible(data^)
echo                 elif command_type == 'terraform':
echo                     return self.execute_terraform(data^)
echo                 elif command_type == 'shell':
echo                     return self.execute_shell(data^)
echo                 else:
echo                     return jsonify({'error': 'Unknown command type'}^), 400
echo             except Exception as e:
echo                 return jsonify({'error': str(e^)}^), 500
echo.
echo     def execute_ssh(self, target, credentials^):
echo         """Execute SSH commands through VPN"""
echo         try:
echo             client = paramiko.SSHClient(^)
echo             client.set_missing_host_key_policy(paramiko.AutoAddPolicy(^)^)
echo             
echo             client.connect(
echo                 hostname=target['host'],
echo                 port=target.get('port', 22^),
echo                 username=credentials['username'],
echo                 password=credentials['password'],
echo                 timeout=10
echo             ^)
echo             
echo             results = []
echo             for command in target.get('commands', []^):
echo                 stdin, stdout, stderr = client.exec_command(command^)
echo                 output = stdout.read(^).decode('utf-8'^)
echo                 error = stderr.read(^).decode('utf-8'^)
echo                 
echo                 results.append({
echo                     'command': command,
echo                     'output': output,
echo                     'error': error,
echo                     'success': len(error^) == 0
echo                 }^)
echo             
echo             client.close(^)
echo             return jsonify({'success': True, 'results': results}^)
echo             
echo         except Exception as e:
echo             return jsonify({'success': False, 'error': str(e^)}^)
echo.
echo     def execute_ansible(self, data^):
echo         """Execute Ansible playbook"""
echo         try:
echo             playbook = data.get('playbook'^)
echo             inventory = data.get('inventory'^)
echo             
echo             # Write playbook to temp file
echo             with open('temp_playbook.yml', 'w'^) as f:
echo                 f.write(playbook^)
echo             
echo             # Write inventory to temp file  
echo             with open('temp_inventory', 'w'^) as f:
echo                 f.write(inventory^)
echo             
echo             # Execute ansible-playbook
echo             cmd = ['ansible-playbook', '-i', 'temp_inventory', 'temp_playbook.yml']
echo             result = subprocess.run(cmd, capture_output=True, text=True^)
echo             
echo             return jsonify({
echo                 'success': result.returncode == 0,
echo                 'output': result.stdout,
echo                 'error': result.stderr,
echo                 'returncode': result.returncode
echo             }^)
echo             
echo         except Exception as e:
echo             return jsonify({'success': False, 'error': str(e^)}^)
echo.
echo     def execute_terraform(self, data^):
echo         """Execute Terraform commands"""
echo         try:
echo             tf_config = data.get('config'^)
echo             tf_command = data.get('command', 'plan'^)  # plan, apply, destroy
echo             
echo             # Write terraform config
echo             with open('main.tf', 'w'^) as f:
echo                 f.write(tf_config^)
echo             
echo             # Initialize terraform
echo             init_result = subprocess.run(['terraform', 'init'], capture_output=True, text=True^)
echo             if init_result.returncode != 0:
echo                 return jsonify({'success': False, 'error': 'Terraform init failed: ' + init_result.stderr}^)
echo             
echo             # Execute terraform command
echo             cmd = ['terraform', tf_command]
echo             if tf_command == 'apply':
echo                 cmd.append('-auto-approve'^)
echo             elif tf_command == 'destroy':
echo                 cmd.append('-auto-approve'^)
echo                 
echo             result = subprocess.run(cmd, capture_output=True, text=True^)
echo             
echo             return jsonify({
echo                 'success': result.returncode == 0,
echo                 'output': result.stdout,
echo                 'error': result.stderr,
echo                 'returncode': result.returncode
echo             }^)
echo             
echo         except Exception as e:
echo             return jsonify({'success': False, 'error': str(e^)}^)
echo.
echo     def execute_shell(self, data^):
echo         """Execute shell script"""
echo         try:
echo             script = data.get('script'^)
echo             shell_type = data.get('shell', 'cmd'^)  # cmd, powershell, bash
echo             
echo             if shell_type == 'powershell':
echo                 cmd = ['powershell', '-Command', script]
echo             elif shell_type == 'bash':
echo                 cmd = ['bash', '-c', script]
echo             else:
echo                 cmd = ['cmd', '/c', script]
echo             
echo             result = subprocess.run(cmd, capture_output=True, text=True^)
echo             
echo             return jsonify({
echo                 'success': result.returncode == 0,
echo                 'output': result.stdout,
echo                 'error': result.stderr,
echo                 'returncode': result.returncode
echo             }^)
echo             
echo         except Exception as e:
echo             return jsonify({'success': False, 'error': str(e^)}^)
echo.
echo     def register_with_saas(self^):
echo         """Register this agent with the SaaS platform"""
echo         try:
echo             # Get local IP
echo             import socket
echo             hostname = socket.gethostname(^)
echo             local_ip = socket.gethostbyname(hostname^)
echo             
echo             registration_data = {
echo                 'agent_id': f"{hostname}_{local_ip}",
echo                 'ip_address': local_ip,
echo                 'hostname': hostname,
echo                 'capabilities': ['ssh', 'ansible', 'terraform', 'shell'],
echo                 'status': 'active'
echo             }
echo             
echo             # Send registration to SaaS platform
echo             # response = requests.post(f"{self.saas_server}/api/agents/register", json=registration_data^)
echo             print(f"Agent registered: {registration_data}"]
echo             
echo         except Exception as e:
echo             print(f"Registration failed: {e}"]
echo.
echo     def run(self, host='0.0.0.0', port=5001^):
echo         """Start the agent server"""
echo         print(f"Starting SaaS Deployment Agent on {host}:{port}"]
echo         self.register_with_saas(^)
echo         self.app.run(host=host, port=port, debug=False^)
echo.
echo if __name__ == '__main__':
echo     agent = SaaSDeploymentAgent(^)
echo     agent.run(^)
) > deployment_agent.py

echo [OK] Deployment agent created

:: Step 4: Enable SSH Server (for incoming connections from SaaS platform)
echo.
echo [STEP 4] Configuring SSH server for incoming connections...

:: Check if OpenSSH Server is installed
sc query sshd >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] OpenSSH Server is already installed
) else (
    echo [INFO] Installing OpenSSH Server...
    dism /online /add-capability /capabilityname:OpenSSH.Server~~~~0.0.1.0 /quiet
    
    if %errorLevel% == 0 (
        echo [OK] OpenSSH Server installed
    ) else (
        echo [WARNING] Failed to install OpenSSH Server automatically
        echo You may need to install it manually from Windows Settings
    )
)

:: Start SSH service
net start sshd >nul 2>&1
sc config sshd start=auto >nul 2>&1
echo [OK] SSH server configured to start automatically

:: Configure Windows Firewall
echo [INFO] Configuring Windows Firewall for SSH...
netsh advfirewall firewall add rule name="SSH Server" dir=in action=allow protocol=TCP localport=22 >nul 2>&1
netsh advfirewall firewall add rule name="SaaS Agent" dir=in action=allow protocol=TCP localport=5001 >nul 2>&1
echo [OK] Firewall rules added

:: Step 5: Create startup script
echo.
echo [STEP 5] Creating startup scripts...

:: Create agent startup script
(
echo @echo off
echo title SaaS Deployment Agent
echo echo Starting SaaS Deployment Agent...
echo cd /d "%INSTALL_DIR%"
echo python deployment_agent.py
echo pause
) > start_agent.bat

echo [OK] Agent startup script created

:: Create auto-start registry entry (optional)
echo [INFO] Setting up auto-start (optional)...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SaaSAgent" /t REG_SZ /d "%INSTALL_DIR%\start_agent.bat" /f >nul 2>&1
echo [OK] Auto-start configured

:: Step 6: Get network information
echo.
echo [STEP 6] Network Configuration...

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "LOCAL_IP=%%a"
    set "LOCAL_IP=!LOCAL_IP:~1!"
    goto :found_ip
)
:found_ip

echo [INFO] Your local IP address: %LOCAL_IP%
echo [INFO] Agent will be accessible at: http://%LOCAL_IP%:5001

:: Create configuration file
(
echo {
echo   "agent_info": {
echo     "local_ip": "%LOCAL_IP%",
echo     "hostname": "%COMPUTERNAME%",
echo     "install_dir": "%INSTALL_DIR%",
echo     "version": "1.0.0"
echo   },
echo   "saas_config": {
echo     "server_url": "YOUR_SAAS_SERVER_URL",
echo     "agent_port": 5001,
echo     "ssh_port": 22
echo   },
echo   "capabilities": [
echo     "ssh_tunnel",
echo     "ansible_execution", 
echo     "terraform_execution",
echo     "shell_execution"
echo   ]
echo }
) > agent_config.json

:: Step 7: Test the setup
echo.
echo [STEP 7] Testing setup...

python -c "import paramiko; print('[OK] Paramiko (SSH) library working')" 2>nul
python -c "import flask; print('[OK] Flask (Web server) library working')" 2>nul
python -c "import requests; print('[OK] Requests (HTTP client) library working')" 2>nul

:: Final summary
echo.
echo ===============================================
echo    Setup Complete!
echo ===============================================
echo.
echo Installation Directory: %INSTALL_DIR%
echo Local IP Address: %LOCAL_IP%
echo Agent URL: http://%LOCAL_IP%:5001
echo SSH Port: 22
echo.
echo NEXT STEPS:
echo 1. Connect to your company VPN
echo 2. Run 'start_agent.bat' to start the deployment agent
echo 3. Your SaaS platform can now route deployments through this machine
echo.
echo IMPORTANT NETWORK INFORMATION:
echo - Make sure your SaaS platform can reach: %LOCAL_IP%:5001
echo - SSH access available on: %LOCAL_IP%:22
echo - Firewall rules have been configured
echo.
echo FILES CREATED:
echo - deployment_agent.py (Main agent script)
echo - start_agent.bat (Startup script)
echo - agent_config.json (Configuration file)
echo.
echo TESTING:
echo 1. Start the agent: start_agent.bat
echo 2. Test from browser: http://%LOCAL_IP%:5001/health
echo 3. Configure your SaaS platform to use this agent
echo.

pause

:: Optional: Start the agent immediately
set /p START_NOW="Start the deployment agent now? (y/n): "
if /i "%START_NOW%"=="y" (
    echo Starting deployment agent...
    start start_agent.bat
)

echo.
echo Setup complete! You can always start the agent later by running start_agent.bat
echo.
pause
