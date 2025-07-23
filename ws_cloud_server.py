import asyncio
import websockets
import json
import paramiko

async def ssh_execute_linux(host, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password)

        stdin, stdout, stderr = client.exec_command(command)
        result = stdout.read().decode() + stderr.read().decode()
        client.close()
        return result
    except Exception as e:
        return f"SSH failed: {e}"

async def agent():
    uri = "ws://13.58.212.239:8765"  # Replace with actual IP or DNS
    async with websockets.connect(uri) as websocket:
        agent_id = "agent-001"
        await websocket.send(agent_id)
        print(f"Connected to server as {agent_id}")

        while True:
            message = await websocket.recv()
            print(f"Command received: {message}")
            data = json.loads(message)

            if data.get("target") == "private-linux":
                linux_ip = data.get("host", "192.168.32.243")  # Example private IP
                username = data.get("username", "ubuntu")
                password = data.get("password", "Cvbnmjkl@30263")  # Or use SSH key
                cmd = data.get("cmd", "hostname && uptime")
                
                result = await ssh_execute_linux(linux_ip, username, password, cmd)
                await websocket.send(result)
            else:
                await websocket.send("Unknown target")

asyncio.run(agent())
