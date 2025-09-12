import asyncio
import websockets
import json

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0aCIsImV4cCI6MTc1NzczMTM4M30.Sk3L8y6W5saXyk-O210TCWlMOFAHF59wFxvthlrVWss"

# FastAPI WebSocket endpoint
WS_URL = f"wss://fastapi-app-61yp.onrender.com/api/auth/chat/ws?token={ACCESS_TOKEN}"

async def test_chat():
    async with websockets.connect(WS_URL) as websocket:
        print("✅ Connected to WebSocket")

        # Send a chat messages
        message_data = {
            "action": "message",
            "receiver_id": "6f1e0446-2681-49a2-8020-4323f4ac1f0f",  # Replace with the receiver's user_id
            "content": "Hello from Python client!"
        }
        await websocket.send(json.dumps(message_data))
        print("📤 Message sent!")

        # Send typing indicator
        typing_data = {
            "action": "typing",
            "receiver_id": "6f1e0446-2681-49a2-8020-4323f4ac1f0f"
        }
        await websocket.send(json.dumps(typing_data))
        print("📤 Typing indicator sent!")

        # Listen for messages
        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print("📥 Received:", data)
        except websockets.exceptions.ConnectionClosed:
            print("⚠️ WebSocket connection closed")

if __name__ == "__main__":
    asyncio.run(test_chat())
