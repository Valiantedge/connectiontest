import asyncio
import websockets
import json
import paramiko

agent_id = "agent-001"
server_url = "ws://13.58.212.239:8765"  # Replace with your server's IP or hostname

async def ssh_execute_command(host, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password)

        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode()
        err = stderr.read().decode()
        rc = stdout.channel.recv_exit_status()
        client.close()

        return {"stdout": out, "stderr": err, "returncode": rc}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

async def agent():
    async with websockets.connect(server_url) as websocket:
        print(f"Connected to cloud as {agent_id}")
        await websocket.send(agent_id)

        async for message in websocket:
            command_data = json.loads(message)
            print(f"Received command: {command_data}")
            result = await ssh_execute_command(
                command_data["host"],
                command_data["username"],
                command_data["password"],
                command_data["cmd"]
            )
            await websocket.send(json.dumps(result))
            print(f"Sent result: {result}")

asyncio.run(agent())
