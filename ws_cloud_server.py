import asyncio
import websockets
import json

# Stores connected agents
connected_agents = {}

async def handler(websocket):
    try:
        # Wait for agent to send its ID
        agent_id = await websocket.recv()
        print(f"[SERVER] Agent connected: {agent_id}")
        connected_agents[agent_id] = websocket

        async for message in websocket:
            print(f"[SERVER] Message from {agent_id}: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"[SERVER] Agent disconnected: {agent_id}")
        connected_agents.pop(agent_id, None)

async def send_command(agent_id, command_dict):
    if agent_id in connected_agents:
        try:
            ws = connected_agents[agent_id]
            await ws.send(json.dumps(command_dict))
            print(f"[SERVER] Sent command to {agent_id}")
        except Exception as e:
            print(f"[SERVER] Error sending command: {e}")
    else:
        print(f"[SERVER] Agent {agent_id} not connected")

# Example test command after agent connects
async def test_command():
    await asyncio.sleep(5)  # give time for agent to connect
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
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
