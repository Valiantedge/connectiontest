# SSH Connection Tester - Testing Guide

## Your Setup Scenario
- **AWS Server**: Where the Python script runs
- **Your Laptop**: Connected to company VPN, acts as tunnel/bridge
- **Target Server**: On-premise Linux server (accessible via VPN)

## Testing Steps

### Phase 1: Prepare Your Laptop (Windows)

1. **Install Python** (if not already installed):
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. **Enable SSH Server on Windows**:
   ```powershell
   # Run as Administrator
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Start-Service sshd
   Set-Service -Name sshd -StartupType 'Automatic'
   
   # Allow through firewall
   New-NetFirewallRule -DisplayName 'OpenSSH-Server-In-TCP' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow
   ```

3. **Test SSH access to your laptop**:
   ```powershell
   # From another machine, test:
   ssh YOUR_WINDOWS_USERNAME@YOUR_LAPTOP_IP
   ```

4. **Connect to company VPN** and verify you can reach the target server:
   ```powershell
   ping TARGET_SERVER_IP
   ```

### Phase 2: Setup AWS Server

1. **Copy files to AWS server**:
   ```bash
   # Copy all Python files to your AWS server
   scp *.py ec2-user@your-aws-server:/home/ec2-user/
   scp requirements.txt ec2-user@your-aws-server:/home/ec2-user/
   ```

2. **Install dependencies on AWS**:
   ```bash
   # On AWS server
   sudo yum update -y
   sudo yum install -y python3 python3-pip
   pip3 install --user paramiko
   ```

### Phase 3: Test Connectivity

1. **From AWS server, test laptop connectivity**:
   ```bash
   # Test if laptop is reachable
   ping YOUR_LAPTOP_IP
   
   # Test SSH access to laptop
   ssh YOUR_WINDOWS_USERNAME@YOUR_LAPTOP_IP
   ```

2. **From your laptop, test target server** (with VPN connected):
   ```powershell
   ping TARGET_SERVER_IP
   ssh TARGET_USER@TARGET_SERVER_IP
   ```

### Phase 4: Run the Tests

#### Option A: Command Line Version (Recommended for AWS)

```bash
# On AWS server - Direct connection test (this will likely fail)
python3 ssh_tester_cli.py --server TARGET_SERVER_IP --username TARGET_USER --password

# On AWS server - Tunneled connection through your laptop
python3 ssh_tester_cli.py \
  --server TARGET_SERVER_IP --username TARGET_USER --password \
  --tunnel-host YOUR_LAPTOP_IP --tunnel-user YOUR_WINDOWS_USERNAME
```

#### Option B: GUI Version (if you have X11 forwarding)

```bash
# SSH to AWS with X11 forwarding
ssh -X ec2-user@your-aws-server

# Run GUI
python3 ssh_connection_tester.py
```

## Example Test Commands

### Replace these with your actual values:
- `YOUR_LAPTOP_IP`: Your laptop's IP (e.g., 10.0.1.100)
- `YOUR_WINDOWS_USERNAME`: Your Windows username
- `TARGET_SERVER_IP`: On-premise server IP (e.g., 192.168.1.50)
- `TARGET_USER`: Username on target server

### Test 1: Basic connectivity
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.50 --username admin \
  --tunnel-host 10.0.1.100 --tunnel-user myuser \
  --commands "hostname" "uptime"
```

### Test 2: System information
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.50 --username admin \
  --tunnel-host 10.0.1.100 --tunnel-user myuser \
  --commands "uname -a" "free -h" "df -h" "ps aux | head -10"
```

### Test 3: Network information
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.50 --username admin \
  --tunnel-host 10.0.1.100 --tunnel-user myuser \
  --commands "ip addr show" "netstat -tuln" "route -n"
```

## Troubleshooting

### Common Issues:

1. **"Connection refused" to laptop**:
   - Ensure SSH server is running on Windows
   - Check Windows Firewall settings
   - Verify laptop IP is correct

2. **"Authentication failed" for laptop**:
   - Use your Windows account username/password
   - Try enabling password authentication in SSH config

3. **"Connection timeout" to target server**:
   - Ensure VPN is connected on laptop
   - Verify target server IP is reachable from laptop

4. **"Permission denied" on target server**:
   - Verify target server credentials
   - Check if SSH is enabled on target server

### Debug Commands:

```bash
# Check if laptop SSH is accessible
telnet YOUR_LAPTOP_IP 22

# Test manual SSH tunnel
ssh -L 2222:TARGET_SERVER_IP:22 YOUR_WINDOWS_USERNAME@YOUR_LAPTOP_IP

# In another terminal, test tunneled connection
ssh -p 2222 TARGET_USER@localhost
```

## Expected Output

When successful, you should see:
```
[14:30:15] INFO: Starting SSH connection test...
[14:30:15] INFO: Using SSH tunnel through: myuser@10.0.1.100:22
[14:30:15] INFO: Target server: admin@192.168.1.50:22
[14:30:15] INFO: Establishing SSH tunnel...
[14:30:16] SUCCESS: ✓ SSH tunnel established!
[14:30:16] INFO: Creating tunnel channel to 192.168.1.50:22...
[14:30:16] INFO: Connecting to target server through tunnel...
[14:30:17] SUCCESS: ✓ SSH connection to target server established successfully!
[14:30:17] INFO: Executing: hostname
[14:30:17] OUTPUT: server01.company.local
--------------------------------------------------
[14:30:17] INFO: Executing: uptime
[14:30:17] OUTPUT:  14:30:17 up 45 days,  3:22,  2 users,  load average: 0.15, 0.12, 0.09
--------------------------------------------------
[14:30:17] SUCCESS: ✓ All commands executed successfully!
```
