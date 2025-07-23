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
    while True:
        try:
            async with websockets.connect(WEBSOCKET_SERVER) as ws:
                await ws.send(AGENT_ID)  # Initial registration
                print(f"[AGENT] Connected to cloud as {AGENT_ID}")

                async for message in ws:
                    data = json.loads(message)

                    # Expecting a command dict
                    if all(k in data for k in ("host", "username", "password", "cmd")):
                        print("[AGENT] Received command:", data)

                        result = await run_ssh_command(
                            data["host"],
                            data["username"],
                            data["password"],
                            data["cmd"]
                        )

                        await ws.send(json.dumps({
                            "agent_id": AGENT_ID,
                            "result": result
                        }))
                        print("[AGENT] Sent result:", result)
        except Exception as e:
            print(f"[AGENT] Error or disconnected: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(agent())
