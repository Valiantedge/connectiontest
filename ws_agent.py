import asyncio
import websockets
import json
import paramiko

AGENT_ID = "agent-001"
CLOUD_WS = "ws://13.58.212.239:8765"  # Replace with actual IP

async def run_ssh_command(host, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        return {
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
            "returncode": 0
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1
        }

async def agent():
    async with websockets.connect(CLOUD_WS) as websocket:
        print(f"Connected to cloud as {AGENT_ID}")
        await websocket.send(AGENT_ID)

        async for message in websocket:
            command = json.loads(message)
            print(f"Received command: {command}")

            result = await run_ssh_command(
                command['host'],
                command['username'],
                command['password'],
                command['cmd']
            )

            print(f"Sent result: {result}")
            await websocket.send(json.dumps(result))

asyncio.run(agent())
