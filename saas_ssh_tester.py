#!/usr/bin/env python3
"""
SaaS SSH Connection Testing Service
Backend service for SaaS platforms to test SSH connectivity to users' private networks
through VPN-connected client machines
"""

import paramiko
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import queue
import time

class SaaSSSHConnectionTester:
    """
    SSH Connection Testing Service for SaaS Applications
    
    This service runs on your SaaS backend (AWS/Cloud) and tests SSH connections
    to users' private network servers through their VPN-connected machines.
    """
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the service"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('ssh_connection_tests.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_ssh_connection(self, connection_config: Dict) -> Dict:
        """
        Test SSH connection with the provided configuration
        
        Args:
            connection_config: Dictionary containing connection parameters
            
        Returns:
            Dictionary with test results
        """
        
        # Validate configuration
        validation_result = self._validate_config(connection_config)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'test_id': connection_config.get('test_id', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
        
        test_id = connection_config.get('test_id', f"test_{int(time.time())}")
        self.logger.info(f"Starting SSH connection test {test_id}")
        
        ssh_client = None
        tunnel_client = None
        results = {
            'success': False,
            'test_id': test_id,
            'timestamp': datetime.now().isoformat(),
            'steps': [],
            'commands_output': [],
            'error': None,
            'connection_time': None
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Extract configuration
            target_server = connection_config['target_server']
            tunnel_config = connection_config.get('tunnel', {})
            commands = connection_config.get('commands', ['hostname', 'uptime'])
            
            self._add_step(results, "Configuration validated", "success")
            
            if tunnel_config.get('enabled', False):
                # Step 2: Establish tunnel to user's VPN-connected machine
                self._add_step(results, "Establishing SSH tunnel to user's machine", "info")
                
                tunnel_client = paramiko.SSHClient()
                tunnel_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                tunnel_client.connect(
                    hostname=tunnel_config['host'],
                    port=tunnel_config.get('port', 22),
                    username=tunnel_config['username'],
                    password=tunnel_config['password'],
                    timeout=10
                )
                
                self._add_step(results, "SSH tunnel established successfully", "success")
                
                # Step 3: Create tunnel channel to target server
                transport = tunnel_client.get_transport()
                dest_addr = (target_server['host'], target_server['port'])
                local_addr = ('127.0.0.1', 0)
                
                self._add_step(results, f"Creating tunnel channel to {dest_addr[0]}:{dest_addr[1]}", "info")
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
                
                # Step 4: Connect to target server through tunnel
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                self._add_step(results, "Connecting to target server through tunnel", "info")
                
                if target_server.get('auth_method') == 'key':
                    ssh_client.connect(
                        hostname=target_server['host'],
                        port=target_server['port'],
                        username=target_server['username'],
                        key_filename=target_server['key_file'],
                        timeout=10,
                        sock=channel
                    )
                else:
                    ssh_client.connect(
                        hostname=target_server['host'],
                        port=target_server['port'],
                        username=target_server['username'],
                        password=target_server['password'],
                        timeout=10,
                        sock=channel
                    )
            else:
                # Direct connection (no tunnel)
                self._add_step(results, "Establishing direct SSH connection", "info")
                
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if target_server.get('auth_method') == 'key':
                    ssh_client.connect(
                        hostname=target_server['host'],
                        port=target_server['port'],
                        username=target_server['username'],
                        key_filename=target_server['key_file'],
                        timeout=10
                    )
                else:
                    ssh_client.connect(
                        hostname=target_server['host'],
                        port=target_server['port'],
                        username=target_server['username'],
                        password=target_server['password'],
                        timeout=10
                    )
            
            connection_time = time.time() - start_time
            results['connection_time'] = round(connection_time, 2)
            self._add_step(results, f"SSH connection established in {connection_time:.2f}s", "success")
            
            # Step 5: Execute test commands
            for command in commands:
                self._add_step(results, f"Executing: {command}", "info")
                
                stdin, stdout, stderr = ssh_client.exec_command(command)
                
                output = stdout.read().decode('utf-8').strip()
                error = stderr.read().decode('utf-8').strip()
                
                command_result = {
                    'command': command,
                    'output': output,
                    'error': error,
                    'success': len(error) == 0
                }
                
                results['commands_output'].append(command_result)
                
                if output:
                    self._add_step(results, f"Command output: {output[:100]}...", "output")
                if error:
                    self._add_step(results, f"Command error: {error}", "error")
            
            results['success'] = True
            self._add_step(results, "All commands executed successfully", "success")
            
        except paramiko.AuthenticationException as e:
            error_msg = f"Authentication failed: {str(e)}"
            results['error'] = error_msg
            self._add_step(results, error_msg, "error")
            
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error: {str(e)}"
            results['error'] = error_msg
            self._add_step(results, error_msg, "error")
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            results['error'] = error_msg
            self._add_step(results, error_msg, "error")
            
        finally:
            # Cleanup connections
            if ssh_client:
                ssh_client.close()
            if tunnel_client:
                tunnel_client.close()
            
            self.logger.info(f"Test {test_id} completed. Success: {results['success']}")
        
        return results
    
    def _validate_config(self, config: Dict) -> Dict:
        """Validate the connection configuration"""
        
        required_fields = ['target_server']
        for field in required_fields:
            if field not in config:
                return {'valid': False, 'error': f"Missing required field: {field}"}
        
        target_server = config['target_server']
        server_required = ['host', 'username', 'port']
        
        for field in server_required:
            if field not in target_server:
                return {'valid': False, 'error': f"Missing target_server field: {field}"}
        
        # Check authentication
        if target_server.get('auth_method') == 'key':
            if 'key_file' not in target_server:
                return {'valid': False, 'error': "Key file required for key authentication"}
        else:
            if 'password' not in target_server:
                return {'valid': False, 'error': "Password required for password authentication"}
        
        # Validate tunnel config if enabled
        tunnel = config.get('tunnel', {})
        if tunnel.get('enabled', False):
            tunnel_required = ['host', 'username', 'password']
            for field in tunnel_required:
                if field not in tunnel:
                    return {'valid': False, 'error': f"Missing tunnel field: {field}"}
        
        return {'valid': True}
    
    def _add_step(self, results: Dict, message: str, level: str):
        """Add a step to the results"""
        step = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        results['steps'].append(step)
        
        # Log the step
        if level == 'error':
            self.logger.error(f"{results['test_id']}: {message}")
        elif level == 'success':
            self.logger.info(f"{results['test_id']}: ✓ {message}")
        else:
            self.logger.info(f"{results['test_id']}: {message}")

# Example usage for SaaS integration
def test_user_connection(user_config: Dict) -> Dict:
    """
    Main function to test user's SSH connection
    This is what your SaaS backend would call
    """
    tester = SaaSSSHConnectionTester()
    return tester.test_ssh_connection(user_config)

# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SaaS SSH Connection Testing Service")
    parser.add_argument("--config", required=True, help="JSON configuration file")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Read configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading configuration: {e}")
        exit(1)
    
    # Run the test
    results = test_user_connection(config)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)
