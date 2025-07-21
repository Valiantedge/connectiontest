#!/bin/bash

# Example usage script for SSH Connection Tester
# This demonstrates different ways to use the SSH tester

echo "=== SSH Connection Tester Examples ==="
echo

# Get user input
read -p "Enter your laptop IP address: " LAPTOP_IP
read -p "Enter your laptop username: " LAPTOP_USER
read -p "Enter target server IP: " SERVER_IP
read -p "Enter target server username: " SERVER_USER

echo
echo "=== Available Test Options ==="
echo "1. Test laptop connectivity"
echo "2. Direct connection to server (no tunnel)"
echo "3. Tunneled connection through laptop"
echo "4. Custom commands test"
echo "5. Run GUI version"

read -p "Choose option (1-5): " OPTION

case $OPTION in
    1)
        echo "Testing connectivity to your laptop..."
        ping -c 3 $LAPTOP_IP
        echo "Testing SSH port on laptop..."
        timeout 5 bash -c "echo >/dev/tcp/$LAPTOP_IP/22" && echo "SSH port is open" || echo "SSH port is closed"
        ;;
    2)
        echo "Testing direct connection (no tunnel)..."
        python3 ssh_tester_cli.py --server $SERVER_IP --username $SERVER_USER --password
        ;;
    3)
        echo "Testing tunneled connection through laptop..."
        python3 ssh_tester_cli.py \
            --server $SERVER_IP --username $SERVER_USER --password \
            --tunnel-host $LAPTOP_IP --tunnel-user $LAPTOP_USER
        ;;
    4)
        echo "Testing with custom commands..."
        python3 ssh_tester_cli.py \
            --server $SERVER_IP --username $SERVER_USER --password \
            --tunnel-host $LAPTOP_IP --tunnel-user $LAPTOP_USER \
            --commands "uname -a" "cat /etc/os-release" "netstat -tuln | grep :22"
        ;;
    5)
        echo "Starting GUI version..."
        python3 ssh_connection_tester.py
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
