import asyncio
import websockets

URI = "ws://127.0.0.1:8000/interaction/chat"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVmOGQ2OGJkLTJkYzgtNGUyYi1hY2IxLTZlZGM0ODRkMTJmMCIsImVtYWlsIjoibG9naW5AZW1haWwuY29tIn0.vABeYx-_3qelmaTAXIkmuips93S1Vd0kZu3aewqEb7Y"


async def run_client(client_id):
    try:
        async with websockets.connect(
            URI, additional_headers={"Authorization": f"Bearer {TOKEN}"}
        ) as websocket:
            print(f"[Client {client_id}] Connected")
            await websocket.send("Tell me a short joke.")
            response = await websocket.recv()
            print(f"[Client {client_id}] Response: {response}")
    except Exception as e:
        print(f"[Client {client_id}] Error: {e}")


async def main():
    await asyncio.gather(*(run_client(i) for i in range(200)))


asyncio.run(main())
