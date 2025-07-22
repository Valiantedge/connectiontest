import asyncio
import websockets
import json

connected_agents = {}

async def handler(websocket, path):
    # Register agent
    agent_id = await websocket.recv()
    connected_agents[agent_id] = websocket
    print(f"Agent {agent_id} connected.")
    try:
        while True:
            # Wait for command from UI/API (simulate with input for demo)
            command = await websocket.recv()
            print(f"Received from agent {agent_id}: {command}")
            # Here, you could process results sent by agent
    except websockets.ConnectionClosed:
        print(f"Agent {agent_id} disconnected.")
        del connected_agents[agent_id]

async def send_command(agent_id, command):
    ws = connected_agents.get(agent_id)
    if ws:
        await ws.send(json.dumps(command))
        print(f"Sent command to agent {agent_id}")
    else:
        print(f"Agent {agent_id} not connected.")

if __name__ == "__main__":
    start_server = websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server running on port 8765...")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
