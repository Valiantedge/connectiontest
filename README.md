# SSH Connection Tester with VPN Tunnel Support

A Python GUI application to test SSH connections to on-premise Linux servers, with support for SSH tunneling through a laptop connected to VPN.

## Features

- **User-friendly GUI** with input fields for connection details
- **SSH Tunneling Support** - Connect through your VPN-connected laptop from AWS/remote servers
- **Two authentication methods**: Password or Private Key (for target server)
- **Customizable commands** to execute on the remote server
- **Real-time output** with timestamps and status levels
- **Error handling** for connection failures
- **Output saving** to text files
- **Progress indication** during connection attempts

## Use Cases

### Scenario 1: Direct Connection
- Run the script on your laptop (connected to VPN)
- Connect directly to on-premise servers

### Scenario 2: Tunneled Connection (Your Setup)
- Run the script on AWS server or any remote machine
- Tunnel SSH connections through your VPN-connected laptop
- Your laptop acts as a bridge to reach on-premise servers

## Prerequisites

- Python 3.6 or higher
- For tunneling: SSH access to your laptop from the AWS server
- Network connectivity to the target server (VPN connection if required on the laptop)

## Installation

1. **Clone or download** this repository to your local machine

2. **Install dependencies** using one of these methods:

   **Option A: Using the batch file (Windows)**
   ```
   double-click run_ssh_tester.bat
   ```

   **Option B: Manual installation**
   ```bash
   pip install -r requirements.txt
   ```

   **Option C: Install paramiko directly**
   ```bash
   pip install paramiko
   ```

## Usage

### GUI Version (Windows/Desktop)

**Option A: Using the batch file**
```
double-click run_ssh_tester.bat
```

**Option B: Direct Python execution**
```bash
python ssh_connection_tester.py
```

### Command Line Version (Headless Servers)

For AWS servers or headless environments without GUI support:

**Direct connection example:**
```bash
python3 ssh_tester_cli.py --server 192.168.1.100 --username admin --password
```

**Tunneled connection example:**
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.100 --username admin --password \
  --tunnel-host YOUR_LAPTOP_IP --tunnel-user YOUR_LAPTOP_USER
```

**Using private key:**
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.100 --username admin --keyfile /path/to/key.pem \
  --tunnel-host YOUR_LAPTOP_IP --tunnel-user YOUR_LAPTOP_USER
```

**Custom commands:**
```bash
python3 ssh_tester_cli.py \
  --server 192.168.1.100 --username admin --password \
  --tunnel-host YOUR_LAPTOP_IP --tunnel-user YOUR_LAPTOP_USER \
  --commands "uname -a" "free -h" "ps aux | head -10"
```

#### CLI Options:
- `--server`: Target server IP address (required)
- `--username`: Username for target server (required)
- `--password`: Password for target server (will prompt if not provided)
- `--keyfile`: Private key file for target server
- `--port`: SSH port for target server (default: 22)
- `--tunnel-host`: Laptop IP address for SSH tunnel
- `--tunnel-user`: Username for laptop
- `--tunnel-pass`: Password for laptop (will prompt if not provided)
- `--tunnel-port`: SSH port for laptop (default: 22)
- `--commands`: Commands to execute (default: hostname, uptime, whoami, df -h)

### Using the GUI

1. **Connection Details**:
   - Enter the target server's private IP address
   - Specify the SSH port (default: 22)
   - Enter your username for the target server

2. **SSH Tunnel (Optional)**:
   - Check "Use SSH Tunnel through laptop" if running from AWS/remote server
   - **Laptop IP**: Enter your laptop's IP address (accessible from AWS server)
   - **SSH Port**: SSH port on your laptop (usually 22)
   - **Laptop User**: Your username on the laptop
   - **Laptop Password**: Your password for the laptop

3. **Target Server Authentication**:
   - **Password**: Select this option and enter your target server password
   - **Private Key**: Select this option and browse to your private key file

4. **Commands to Execute**:
   - The default commands are: `hostname`, `uptime`, `whoami`, `df -h`
   - You can modify these commands as needed
   - Each command should be on a separate line

5. **Testing Connection**:
   - Click "Test SSH Connection" to start the test
   - Monitor the output panel for real-time results
   - Use "Clear Output" to clear the results
   - Use "Save Output" to save results to a file

## Connection Flow

### Direct Connection (No Tunnel)
```
AWS Server → Target On-Prem Server
```

### Tunneled Connection (Through Laptop)
```
AWS Server → Your Laptop (VPN) → Target On-Prem Server
```

The script creates an SSH tunnel from AWS server to your laptop, then forwards the connection to the target server through your laptop's VPN connection.

### Default Commands Executed

- `hostname` - Shows the server's hostname
- `uptime` - Shows system uptime and load
- `whoami` - Shows current user
- `df -h` - Shows disk usage in human-readable format

## Troubleshooting

### Common Issues

1. **"paramiko not found" error**:
   - Install paramiko: `pip install paramiko`

2. **Connection timeout**:
   - **Direct**: Verify VPN connection is active on your machine
   - **Tunneled**: Verify AWS server can reach your laptop, and laptop has VPN active
   - Check if the target server IP is reachable from your laptop
   - Verify firewall settings

3. **Authentication failed**:
   - Double-check username and password for both laptop and target server
   - For key authentication, ensure the private key file is correct
   - Verify the key file permissions

4. **Tunnel connection failed**:
   - Ensure SSH is enabled on your laptop
   - Verify your laptop's IP is accessible from the AWS server
   - Check Windows firewall settings on your laptop
   - Ensure your laptop user has SSH login permissions

5. **Permission denied**:
   - Ensure your user account has SSH access on the target server
   - Check if SSH service is running on the target server

### Network Connectivity Test

Before using the SSH tester, verify basic connectivity:

**From AWS Server to Laptop:**
```bash
# Test if laptop is reachable
ping [laptop-ip]

# Test if SSH port is open on laptop
telnet [laptop-ip] 22
```

**From Laptop to Target Server:**
```bash
# Test if server is reachable (with VPN connected)
ping [server-ip]

# Test if SSH port is open
telnet [server-ip] 22
```

## Setup for Tunneling

### On Your Laptop (Windows):
1. **Enable SSH Server** (if not already):
   - Install OpenSSH Server through Windows Features or:
   ```powershell
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Start-Service sshd
   Set-Service -Name sshd -StartupType 'Automatic'
   ```

2. **Configure Windows Firewall**:
   - Allow SSH (port 22) through Windows Firewall
   - Or use: `New-NetFirewallRule -DisplayName 'OpenSSH-Server-In-TCP' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow`

3. **Connect to VPN** before running tests

### On AWS Server:
1. Install Python and paramiko
2. Run the SSH tester script
3. Configure tunnel settings to point to your laptop

## Security Notes

- **Passwords are not stored** - they exist only in memory during execution
- **Private keys should be properly secured** with appropriate file permissions
- **Use strong authentication methods** when possible
- **Consider using key-based authentication** instead of passwords for better security

## Output Format

The application provides timestamped output with different levels:
- **INFO**: General information messages
- **SUCCESS**: Successful operations
- **OUTPUT**: Command output from the server
- **ERROR**: Error messages and failures

## Example Output

```
[14:30:15] INFO: Starting SSH connection test...
[14:30:15] INFO: Target: admin@192.168.1.100:22
[14:30:15] INFO: Establishing SSH connection...
[14:30:16] SUCCESS: ✓ SSH connection established successfully!
[14:30:16] INFO: Executing: hostname
[14:30:16] OUTPUT:
server01.company.local
[14:30:16] INFO: --------------------------------------------------
[14:30:16] INFO: Executing: uptime
[14:30:16] OUTPUT:
 14:30:16 up 45 days,  3:22,  2 users,  load average: 0.15, 0.12, 0.09
[14:30:16] SUCCESS: ✓ All commands executed successfully!
```

## License

This project is open source and available under the MIT License.
