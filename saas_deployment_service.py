"""
SaaS SSH Connection Testing Service
For Ansible/Terraform/Shell script deployment through user VPN connections

This service acts as a bridge between your SaaS platform and user's private networks
"""

import paramiko
import subprocess
import json
import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import queue
import time
from pathlib import Path

class SaaSDeploymentTester:
    """
    Main service for testing deployments through user VPN connections
    """
    
    def __init__(self, work_dir="/tmp/saas_deployments"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the service"""
        log_file = self.work_dir / "deployment_tests.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def test_deployment_connectivity(self, config: Dict) -> Dict:
        """
        Test deployment connectivity and run scripts through VPN tunnel
        
        Args:
            config: Deployment configuration
        Returns:
            Test results with deployment status
        """
        test_id = config.get('test_id', f"deploy_{int(time.time())}")
        results = {
            'success': False,
            'test_id': test_id,
            'timestamp': datetime.now().isoformat(),
            'steps': [],
            'deployment_output': [],
            'error': None,
            'connection_time': None,
            'total_time': None
        }
        start_time = time.time()
        try:
            self.logger.info(f"Starting deployment test {test_id}")
            # Step 1: Test SSH connectivity
            connectivity_result = self._test_ssh_connectivity(config)
            if not connectivity_result.get('success'):
                results['error'] = f"SSH connectivity failed: {connectivity_result.get('error')}"
                return results
            results['steps'].extend(connectivity_result.get('steps', []))
            results['connection_time'] = connectivity_result.get('connection_time')
            # Step 2: Setup SSH tunnel for deployment
            tunnel_info = self._setup_deployment_tunnel(config)
            if not tunnel_info.get('success'):
                results['error'] = f"Tunnel setup failed: {tunnel_info.get('error')}"
                return results
            self._add_step(results, f"Deployment tunnel established on port {tunnel_info.get('local_port')}", "success")
            # Step 3: Execute deployment scripts
            deployment_result = self._execute_deployment(config, tunnel_info.get('local_port'))
            results['deployment_output'] = deployment_result.get('output', [])
            if deployment_result.get('success'):
                results['success'] = True
                self._add_step(results, "Deployment completed successfully", "success")
            else:
                results['error'] = deployment_result.get('error')
                self._add_step(results, f"Deployment failed: {deployment_result.get('error')}", "error")
        except Exception as e:
            results['error'] = str(e)
            self._add_step(results, f"Deployment test failed: {str(e)}", "error")
        results['total_time'] = round(time.time() - start_time, 2)
        return results

    def _test_ssh_connectivity(self, config: Dict) -> Dict:
        """Test basic SSH connectivity"""
        
        result = {'success': False, 'steps': [], 'error': None}
        
        try:
            target_server = config['target_server']
            tunnel_config = config.get('tunnel', {})
            
            ssh_client = None
            tunnel_client = None
            
            start_time = time.time()
            
            if tunnel_config.get('enabled', False):
                # Test through tunnel
                self._add_step(result, "Testing SSH connectivity through VPN tunnel", "info")
                
                # Connect to user's VPN machine
                tunnel_client = paramiko.SSHClient()
                tunnel_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                tunnel_client.connect(
                    hostname=tunnel_config['host'],
                    port=tunnel_config.get('port', 22),
                    username=tunnel_config['username'],
                    password=tunnel_config['password'],
                    timeout=10
                )
                
                self._add_step(result, "Connected to user's VPN machine", "success")
                
                # Create tunnel to target server
                transport = tunnel_client.get_transport()
                dest_addr = (target_server['host'], target_server['port'])
                local_addr = ('127.0.0.1', 0)
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
                
                # Connect to target server through tunnel
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
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
                # Direct connection
                self._add_step(result, "Testing direct SSH connectivity", "info")
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
            result['connection_time'] = round(connection_time, 2)
            
            # Test basic commands
            stdin, stdout, stderr = ssh_client.exec_command('hostname && whoami')
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            if error:
                result['error'] = f"Command execution failed: {error}"
            else:
                self._add_step(result, f"SSH connectivity verified: {output}", "success")
                result['success'] = True
            
            # Cleanup
            if ssh_client:
                ssh_client.close()
            if tunnel_client:
                tunnel_client.close()
                
        except Exception as e:
            result['error'] = str(e)
            self._add_step(result, f"SSH connectivity test failed: {str(e)}", "error")
        
        return result

    def _setup_deployment_tunnel(self, config: Dict) -> Dict:
        """Setup SSH tunnel for deployment scripts"""
        
        tunnel_config = config.get('tunnel', {})
        target_server = config['target_server']
        
        if not tunnel_config.get('enabled', False):
            return {
                'success': True, 
                'local_port': None,
                'message': 'Direct connection - no tunnel needed'
            }
        
        try:
            # Find available local port
            import socket
            sock = socket.socket()
            sock.bind(('', 0))
            local_port = sock.getsockname()[1]
            sock.close()
            
            # Create SSH tunnel using subprocess (for Ansible/Terraform compatibility)
            tunnel_cmd = [
                'ssh', '-N', '-L', 
                f"{local_port}:{target_server['host']}:{target_server['port']}",
                f"{tunnel_config['username']}@{tunnel_config['host']}",
                '-p', str(tunnel_config.get('port', 22)),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ConnectTimeout=10'
            ]
            
            # Start tunnel process
            tunnel_process = subprocess.Popen(
                tunnel_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give tunnel time to establish
            time.sleep(2)
            
            # Test if tunnel is working
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_result = test_sock.connect_ex(('127.0.0.1', local_port))
            test_sock.close()
            
            if test_result == 0:
                return {
                    'success': True,
                    'local_port': local_port,
                    'process': tunnel_process,
                    'message': f'Tunnel established on port {local_port}'
                }
            else:
                tunnel_process.terminate()
                return {
                    'success': False,
                    'error': 'Tunnel connection failed'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Tunnel setup failed: {str(e)}'
            }

    def _execute_deployment(self, config: Dict, tunnel_port: Optional[int]) -> Dict:
        """Execute deployment scripts (Ansible/Terraform/Shell)"""
        
        deployment = config.get('deployment', {})
        script_type = deployment.get('type', 'shell')  # ansible, terraform, shell
        
        result = {
            'success': False,
            'output': [],
            'error': None
        }
        
        try:
            if script_type == 'ansible':
                result = self._run_ansible_playbook(config, tunnel_port)
            elif script_type == 'terraform':
                result = self._run_terraform(config, tunnel_port)
            elif script_type == 'shell':
                result = self._run_shell_script(config, tunnel_port)
            else:
                result['error'] = f"Unsupported deployment type: {script_type}"
        
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def _run_ansible_playbook(self, config: Dict, tunnel_port: Optional[int]) -> Dict:
        """Run Ansible playbook through tunnel"""
        
        deployment = config['deployment']
        target_server = config['target_server']
        
        # Create temporary inventory file
        inventory_content = f"""
[target]
{target_server['host']}:{target_server['port']}

[target:vars]
ansible_user={target_server['username']}
ansible_ssh_pass={target_server.get('password', '')}
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
"""
        
        if tunnel_port:
            inventory_content += f"ansible_port={tunnel_port}\n"
            inventory_content += f"ansible_host=127.0.0.1\n"
        
        # Write inventory to temp file
        inventory_file = self.work_dir / f"inventory_{config['test_id']}"
        inventory_file.write_text(inventory_content)
        
        # Write playbook to temp file
        playbook_content = deployment.get('playbook', {})
        playbook_file = self.work_dir / f"playbook_{config['test_id']}.yml"
        
        with open(playbook_file, 'w') as f:
            import yaml
            yaml.dump(playbook_content, f)
        
        # Run ansible-playbook
        cmd = [
            'ansible-playbook',
            '-i', str(inventory_file),
            str(playbook_file),
            '-v'
        ]
        
        return self._run_command(cmd)

    def _run_terraform(self, config: Dict, tunnel_port: Optional[int]) -> Dict:
        """Run Terraform through tunnel"""
        
        deployment = config['deployment']
        
        # Create terraform configuration with tunnel settings
        tf_config = deployment.get('config', {})
        
        if tunnel_port:
            # Modify terraform config to use tunnel
            if 'provider' in tf_config:
                if 'connection' in tf_config['provider']:
                    tf_config['provider']['connection']['host'] = '127.0.0.1'
                    tf_config['provider']['connection']['port'] = tunnel_port
        
        # Write terraform config
        tf_file = self.work_dir / f"main_{config['test_id']}.tf"
        tf_file.write_text(json.dumps(tf_config, indent=2))
        
        # Run terraform commands
        commands = [
            ['terraform', 'init'],
            ['terraform', 'plan'],
            ['terraform', 'apply', '-auto-approve']
        ]
        
        results = []
        for cmd in commands:
            result = self._run_command(cmd, cwd=str(self.work_dir))
            results.append(result)
            if not result['success']:
                return {
                    'success': False,
                    'output': results,
                    'error': result['error']
                }
        
        return {
            'success': True,
            'output': results,
            'error': None
        }

    def _run_shell_script(self, config: Dict, tunnel_port: Optional[int]) -> Dict:
        """Run shell script through tunnel"""
        
        deployment = config['deployment']
        script_content = deployment.get('script', '')
        
        # Add tunnel environment variables if needed
        if tunnel_port:
            script_content = f"""
export TUNNEL_HOST=127.0.0.1
export TUNNEL_PORT={tunnel_port}
export TARGET_HOST={config['target_server']['host']}
export TARGET_PORT={config['target_server']['port']}

{script_content}
"""
        
        # Write script to temp file
        script_file = self.work_dir / f"script_{config['test_id']}.sh"
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        
        # Run script
        return self._run_command(['/bin/bash', str(script_file)])

    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> Dict:
        """Run a system command and capture output"""
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=cwd
            )
            
            return {
                'success': result.returncode == 0,
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'command': ' '.join(cmd),
                'error': 'Command timed out after 5 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'command': ' '.join(cmd),
                'error': str(e)
            }

    def _add_step(self, results: Dict, message: str, level: str):
        """Add a step to the results"""
        step = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        results['steps'].append(step)
        
        if level == 'error':
            self.logger.error(f"{results['test_id']}: {message}")
        elif level == 'success':
            self.logger.info(f"{results['test_id']}: ✓ {message}")
        else:
            self.logger.info(f"{results['test_id']}: {message}")

# Main function for SaaS integration
def test_deployment(deployment_config: Dict) -> Dict:
    """
    Main function to test deployment through VPN
    """
    tester = SaaSDeploymentTester()
    return tester.test_deployment_connectivity(deployment_config)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SaaS Deployment Testing Service")
    parser.add_argument("--config", required=True, help="JSON deployment configuration file")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading configuration: {e}")
        exit(1)
    
    results = test_deployment(config)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))
    
    exit(0 if results['success'] else 1)
