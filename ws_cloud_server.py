import asyncio
import websockets
import json

connected_agents = {}

async def handler(websocket):  # updated to use only one argument
    agent_id = await websocket.recv()
    connected_agents[agent_id] = websocket
    print(f"Agent {agent_id} connected.")

    try:
        while True:
            await asyncio.sleep(1)  # Keep the connection alive
    except websockets.ConnectionClosed:
        print(f"Agent {agent_id} disconnected.")
        del connected_agents[agent_id]

async def send_command(agent_id, command):
    ws = connected_agents.get(agent_id)
    if ws:
        await ws.send(json.dumps(command))
        print(f"Sent command to agent {agent_id}")
        # Optionally wait for response:
        response = await ws.recv()
        print(f"Received response from {agent_id}: {response}")
    else:
        print(f"Agent {agent_id} not connected.")

if __name__ == "__main__":
    async def main():
        print("WebSocket server running on port 8765...")
        async with websockets.serve(handler, "0.0.0.0", 8765):
            await asyncio.Future()  # run forever

    asyncio.run(main())
