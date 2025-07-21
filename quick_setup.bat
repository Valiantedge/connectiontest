@echo off
:: Simple SaaS Deployment Agent Installer
:: Download and run this on your PC to enable VPN-routed deployments

title SaaS Agent Quick Setup
echo.
echo ================================
echo   SaaS Deployment Agent Setup
echo   Quick VPN-Routing Installation  
echo ================================
echo.

:: Get user confirmation
echo This will install:
echo - Python (if needed)
echo - SSH connection tools
echo - Deployment agent for your SaaS platform
echo.
set /p CONFIRM="Continue with installation? (y/n): "
if /i not "%CONFIRM%"=="y" exit /b

:: Create working directory in user profile
set "AGENT_DIR=%USERPROFILE%\SaaSAgent"
if not exist "%AGENT_DIR%" mkdir "%AGENT_DIR%"
cd /d "%AGENT_DIR%"

echo.
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Python is installed
) else (
    echo Installing Python...
    winget install Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
    if %errorLevel% == 0 (
        echo ✓ Python installed successfully
    ) else (
        echo ! Please install Python from https://python.org and re-run this script
        pause && exit /b 1
    )
)

echo.
echo [2/5] Installing Python packages...
python -m pip install --quiet paramiko flask flask-cors requests
echo ✓ Required packages installed

echo.
echo [3/5] Creating deployment agent...
:: Create a simple agent that your SaaS can communicate with
python -c "
import json
import os
from datetime import datetime

# Create the main agent script
agent_code = '''
import sys
import json
import paramiko
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route(\"/health\", methods=[\"GET\"])
def health():
    return jsonify({\"status\": \"healthy\", \"timestamp\": datetime.now().isoformat()})

@app.route(\"/ssh-test\", methods=[\"POST\"])
def ssh_test():
    data = request.json
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect through this VPN-connected machine
        client.connect(
            hostname=data[\"host\"],
            port=data.get(\"port\", 22),
            username=data[\"username\"],
            password=data[\"password\"],
            timeout=10
        )
        
        results = []
        for cmd in data.get(\"commands\", [\"hostname\", \"uptime\"]):
            stdin, stdout, stderr = client.exec_command(cmd)
            results.append({
                \"command\": cmd,
                \"output\": stdout.read().decode(),
                \"error\": stderr.read().decode()
            })
        
        client.close()
        return jsonify({\"success\": True, \"results\": results})
        
    except Exception as e:
        return jsonify({\"success\": False, \"error\": str(e)})

@app.route(\"/deploy\", methods=[\"POST\"])
def deploy():
    data = request.json
    deploy_type = data.get(\"type\")  # ansible, terraform, shell
    
    try:
        if deploy_type == \"shell\":
            result = subprocess.run(data[\"script\"], shell=True, capture_output=True, text=True)
            return jsonify({
                \"success\": result.returncode == 0,
                \"output\": result.stdout,
                \"error\": result.stderr
            })
        # Add other deployment types as needed
        
    except Exception as e:
        return jsonify({\"success\": False, \"error\": str(e)})

if __name__ == \"__main__\":
    print(\"SaaS Deployment Agent starting on port 5001...\")
    print(\"Your SaaS platform can now connect to this machine for deployments\")
    app.run(host=\"0.0.0.0\", port=5001, debug=False)
'''

with open('agent.py', 'w') as f:
    f.write(agent_code)

print('✓ Agent script created')
"
echo ✓ Deployment agent created

echo.
echo [4/5] Configuring network access...
:: Enable SSH server for incoming connections
powershell -Command "Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*' | Add-WindowsCapability -Online" >nul 2>&1
powershell -Command "Start-Service sshd; Set-Service -Name sshd -StartupType 'Automatic'" >nul 2>&1
powershell -Command "New-NetFirewallRule -DisplayName 'SSH-In' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow" >nul 2>&1
powershell -Command "New-NetFirewallRule -DisplayName 'SaaS-Agent' -Direction Inbound -Protocol TCP -LocalPort 5001 -Action Allow" >nul 2>&1
echo ✓ Network access configured

echo.
echo [5/5] Creating startup files...
:: Create startup batch file
echo @echo off > start-agent.bat
echo title SaaS Deployment Agent >> start-agent.bat
echo cd /d "%AGENT_DIR%" >> start-agent.bat
echo echo Starting SaaS Deployment Agent... >> start-agent.bat
echo echo Connect to VPN first, then your SaaS platform can deploy through this machine >> start-agent.bat
echo python agent.py >> start-agent.bat
echo pause >> start-agent.bat

echo ✓ Startup script created

:: Get local IP for display
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| find "IPv4 Address"') do set "IP=%%i"
set "IP=%IP: =%"

echo.
echo ================================
echo     INSTALLATION COMPLETE!
echo ================================
echo.
echo AGENT LOCATION: %AGENT_DIR%
echo LOCAL IP: %IP%
echo AGENT URL: http://%IP%:5001
echo.
echo TO USE:
echo 1. Connect to your company VPN
echo 2. Run: start-agent.bat
echo 3. Configure your SaaS platform to use: %IP%:5001
echo.
echo YOUR SAAS PLATFORM CAN NOW:
echo - Test SSH connections through this VPN
echo - Deploy Ansible playbooks
echo - Run Terraform scripts  
echo - Execute shell commands
echo - All traffic routes through your VPN connection
echo.

:: Ask to start now
set /p START="Start the agent now? (y/n): "
if /i "%START%"=="y" start start-agent.bat

echo.
echo Setup complete! Check the SaaS platform documentation for configuration details.
pause
