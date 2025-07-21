#!/usr/bin/env python3
"""
SSH Connection Tester - Command Line Version
A command-line tool to test SSH connections through VPN tunnels
For use on headless servers without GUI support
"""

import paramiko
import sys
import argparse
import getpass
from datetime import datetime

class SSHConnectionTesterCLI:
    def __init__(self):
        self.ssh_client = None
        self.tunnel_client = None
    
    def log_message(self, message, level="INFO"):
        """Print message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_connection(self, server_ip, username, password=None, key_file=None, port=22,
                       tunnel_host=None, tunnel_user=None, tunnel_pass=None, tunnel_port=22,
                       commands=None):
        """Test SSH connection with optional tunneling"""
        
        if commands is None:
            commands = ["hostname", "uptime", "whoami", "df -h"]
        
        try:
            self.log_message("Starting SSH connection test...")
            
            if tunnel_host:
                # Use tunnel
                self.log_message(f"Using SSH tunnel through: {tunnel_user}@{tunnel_host}:{tunnel_port}")
                self.log_message(f"Target server: {username}@{server_ip}:{port}")
                
                # Create tunnel connection first
                self.log_message("Establishing SSH tunnel...")
                self.tunnel_client = paramiko.SSHClient()
                self.tunnel_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.tunnel_client.connect(
                    hostname=tunnel_host,
                    port=tunnel_port,
                    username=tunnel_user,
                    password=tunnel_pass,
                    timeout=10
                )
                self.log_message("✓ SSH tunnel established!", "SUCCESS")
                
                # Create tunnel channel
                transport = self.tunnel_client.get_transport()
                dest_addr = (server_ip, port)
                local_addr = ('127.0.0.1', 0)
                
                self.log_message(f"Creating tunnel channel to {dest_addr[0]}:{dest_addr[1]}...")
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
                
                # Connect through tunnel
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                self.log_message("Connecting to target server through tunnel...")
                if password:
                    self.ssh_client.connect(
                        hostname=server_ip,
                        port=port,
                        username=username,
                        password=password,
                        timeout=10,
                        sock=channel
                    )
                else:
                    self.ssh_client.connect(
                        hostname=server_ip,
                        port=port,
                        username=username,
                        key_filename=key_file,
                        timeout=10,
                        sock=channel
                    )
            else:
                # Direct connection
                self.log_message(f"Direct connection to: {username}@{server_ip}:{port}")
                
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                self.log_message("Establishing SSH connection...")
                if password:
                    self.ssh_client.connect(
                        hostname=server_ip,
                        port=port,
                        username=username,
                        password=password,
                        timeout=10
                    )
                else:
                    self.ssh_client.connect(
                        hostname=server_ip,
                        port=port,
                        username=username,
                        key_filename=key_file,
                        timeout=10
                    )
            
            self.log_message("✓ SSH connection established successfully!", "SUCCESS")
            
            # Execute commands
            for command in commands:
                if command.strip():
                    self.log_message(f"Executing: {command}")
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    
                    output = stdout.read().decode('utf-8').strip()
                    error = stderr.read().decode('utf-8').strip()
                    
                    if output:
                        self.log_message(f"Output:\n{output}", "OUTPUT")
                    if error:
                        self.log_message(f"Error:\n{error}", "ERROR")
                    
                    print("-" * 50)
            
            self.log_message("✓ All commands executed successfully!", "SUCCESS")
            return True
            
        except paramiko.AuthenticationException:
            self.log_message("Authentication failed. Please check your credentials.", "ERROR")
            return False
            
        except paramiko.SSHException as e:
            self.log_message(f"SSH connection error: {str(e)}", "ERROR")
            return False
            
        except Exception as e:
            self.log_message(f"Connection failed: {str(e)}", "ERROR")
            return False
            
        finally:
            if self.ssh_client:
                self.ssh_client.close()
            if self.tunnel_client:
                self.tunnel_client.close()

def main():
    parser = argparse.ArgumentParser(description="SSH Connection Tester with Tunnel Support")
    
    # Target server arguments
    parser.add_argument("--server", required=True, help="Target server IP address")
    parser.add_argument("--username", required=True, help="Username for target server")
    parser.add_argument("--port", type=int, default=22, help="SSH port for target server (default: 22)")
    parser.add_argument("--password", help="Password for target server (will prompt if not provided)")
    parser.add_argument("--keyfile", help="Private key file for target server")
    
    # Tunnel arguments
    parser.add_argument("--tunnel-host", help="Laptop IP address for SSH tunnel")
    parser.add_argument("--tunnel-user", help="Username for laptop")
    parser.add_argument("--tunnel-port", type=int, default=22, help="SSH port for laptop (default: 22)")
    parser.add_argument("--tunnel-pass", help="Password for laptop (will prompt if not provided)")
    
    # Command arguments
    parser.add_argument("--commands", nargs="*", default=["hostname", "uptime", "whoami", "df -h"],
                       help="Commands to execute on target server")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.password and not args.keyfile:
        print("Error: Either --password or --keyfile must be provided for target server")
        sys.exit(1)
    
    if args.tunnel_host and not args.tunnel_user:
        print("Error: --tunnel-user is required when using --tunnel-host")
        sys.exit(1)
    
    # Get passwords if not provided
    target_password = args.password
    if not target_password and not args.keyfile:
        target_password = getpass.getpass("Enter password for target server: ")
    
    tunnel_password = args.tunnel_pass
    if args.tunnel_host and not tunnel_password:
        tunnel_password = getpass.getpass("Enter password for laptop: ")
    
    # Run the test
    tester = SSHConnectionTesterCLI()
    success = tester.test_connection(
        server_ip=args.server,
        username=args.username,
        password=target_password,
        key_file=args.keyfile,
        port=args.port,
        tunnel_host=args.tunnel_host,
        tunnel_user=args.tunnel_user,
        tunnel_pass=tunnel_password,
        tunnel_port=args.tunnel_port,
        commands=args.commands
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
