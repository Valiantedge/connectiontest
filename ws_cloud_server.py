# ws_cloud_server.py (your current version is fine)
import asyncio
import websockets
import json

connected_agents = {}

async def handler(websocket):
    try:
        agent_id = await websocket.recv()
        print(f"[SERVER] Agent connected: {agent_id}")
        connected_agents[agent_id] = websocket

        async for message in websocket:
            print(f"[SERVER] Message from {agent_id}: {message}")
            try:
                data = json.loads(message)
                # If the message contains a 'run_local' command, execute it on the cloud server
                if data.get("run_local"):
                    import subprocess
                    cmd = data["run_local"]
                    print(f"[SERVER] Running local command: {cmd}")
                    # If the command is 'deploy.sh', run it from the current directory
                    if cmd == "deploy.sh":
                        proc = subprocess.run(["bash", "deploy.sh"], shell=False, capture_output=True, text=True)
                    else:
                        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    print(f"[SERVER] Local stdout: {proc.stdout}")
                    print(f"[SERVER] Local stderr: {proc.stderr}")
            except Exception as e:
                print(f"[SERVER] Error handling message: {e}")
    except websockets.exceptions.ConnectionClosed:
        print(f"[SERVER] Agent disconnected: {agent_id}")
        connected_agents.pop(agent_id, None)

async def send_command(agent_id, command_dict):
    if agent_id in connected_agents:
        ws = connected_agents[agent_id]
        await ws.send(json.dumps(command_dict))
        print(f"[SERVER] Sent command to {agent_id}")
    else:
        print(f"[SERVER] Agent {agent_id} not connected")

async def test_command():
    await asyncio.sleep(5)
    await send_command("agent-001", {
        "host": "192.168.32.243",
        "username": "ubuntu",
        "password": "Cvbnmjkl@30263",
        "cmd": "hostname && uptime"
    })

async def main():
    print("[SERVER] Starting WebSocket server on port 8765...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await test_command()
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
