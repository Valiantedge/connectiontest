import asyncio
import websockets
import paramiko
import json

AGENT_ID = "agent-001"
WEBSOCKET_SERVER = "ws://13.58.212.239:8765"

async def run_ssh_command(host, username, password, cmd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, timeout=10)

        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        returncode = stdout.channel.recv_exit_status()
        client.close()

        return {"stdout": out, "stderr": err, "returncode": returncode}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

async def agent():
    async with websockets.connect(WEBSOCKET_SERVER) as ws:
        await ws.send(json.dumps({"type": "register", "agent_id": AGENT_ID}))
        print(f"Connected to cloud as {AGENT_ID}")

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                if data.get("type") == "command":
                    command = data["command"]
                    print("Received command:", command)

                    result = await run_ssh_command(
                        command["host"],
                        command["username"],
                        command["password"],
                        command["cmd"]
                    )

                    await ws.send(json.dumps({
                        "type": "result",
                        "agent_id": AGENT_ID,
                        "result": result
                    }))
                    print("Sent result:", result)

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Retrying in 5 seconds...")
                await asyncio.sleep(5)
                return await agent()

if __name__ == "__main__":
    asyncio.run(agent())
