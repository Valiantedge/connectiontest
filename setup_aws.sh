#!/bin/bash

# SSH Connection Tester Setup Script for AWS/Remote Server
# Run this script on your AWS server to set up the environment

echo "=== SSH Connection Tester Setup ==="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing..."
    # For Amazon Linux/CentOS/RHEL
    if command -v yum &> /dev/null; then
        sudo yum update -y
        sudo yum install -y python3 python3-pip
    # For Ubuntu/Debian
    elif command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3 python3-pip
    else
        echo "Please install Python3 manually"
        exit 1
    fi
else
    echo "✓ Python3 is installed"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Installing..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    rm get-pip.py
else
    echo "✓ pip3 is installed"
fi

# Install required packages
echo "Installing required Python packages..."
pip3 install --user paramiko

# Check if tkinter is available (for GUI)
echo "Checking GUI support..."
python3 -c "import tkinter" 2>/dev/null && echo "✓ GUI support available" || echo "⚠ GUI support not available - you may need to install python3-tkinter"

# If GUI is not available, suggest alternatives
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo
    echo "GUI may not work on headless servers. Consider:"
    echo "1. Use X11 forwarding: ssh -X user@aws-server"
    echo "2. Install tkinter: sudo yum install tkinter (CentOS/RHEL) or sudo apt install python3-tkinter (Ubuntu/Debian)"
    echo "3. Run the script with DISPLAY forwarding"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. Ensure your laptop has SSH server running and is accessible"
echo "2. Connect your laptop to VPN"
echo "3. Run the SSH tester: python3 ssh_connection_tester.py"
echo
echo "Network connectivity test commands:"
echo "  ping [your-laptop-ip]"
echo "  telnet [your-laptop-ip] 22"
