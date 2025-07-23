import asyncio
import websockets
import json
import paramiko

async def run():
    uri = "ws://13.58.212.239:8765"  # replace with actual IP
    agent_id = "agent-001"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to cloud as {agent_id}")
        await websocket.send(agent_id)

        while True:
            msg = await websocket.recv()
            command = json.loads(msg)
            print(f"Received command: {command}")

            # Extract SSH details
            host = command.get("host")
            username = command.get("username")
            password = command.get("password")
            cmd = command.get("cmd")

            # SSH and execute
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=username, password=password)

                stdin, stdout, stderr = ssh.exec_command(cmd)
                result = {
                    "stdout": stdout.read().decode(),
                    "stderr": stderr.read().decode(),
                    "returncode": 0
                }
                ssh.close()
            except Exception as e:
                result = {
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": 1
                }

            await websocket.send(json.dumps(result))
            print("Sent result:", result)

asyncio.run(run())
