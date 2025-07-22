# Agent TCP Proxy

This agent acts as a transparent TCP proxy for backend-initiated SSH/Ansible connections.

## Usage
1. Edit `agent_tcp_proxy.py` and set `FORWARD_HOST` to your private server IP.
2. Run the proxy on your agent (Windows laptop):
   ```bash
   python agent_tcp_proxy.py
   ```
3. On your backend, SSH to the agent's IP and port 2222:
   ```bash
   ssh -p 2222 privateuser@AGENT_LAPTOP_IP
   ```
   Or set your Ansible inventory to use the agent's IP and port as the target.

## Notes
- This is a basic TCP proxy. For production, use a secure SSH jump host if possible.
- Adjust firewall rules on the agent to allow incoming connections.
- You can run multiple proxies for multiple clients by changing the port and forward IP.
