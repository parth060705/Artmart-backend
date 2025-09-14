import asyncio
import websockets
import json
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0aCIsImV4cCI6MTc1Nzg4NzE1OX0.uIhbLN41rkNTEkczp7ELlYEmjpfKTRWRPoM7Sg-lr5w"
WS_URL = f"ws://127.0.0.1:8000/api/auth/chat/ws?token={ACCESS_TOKEN}"
RECEIVER_ID = "PUT_RECEIVER_USER_ID_HERE"  # replace with actual receiver

# -----------------------------
# WEBSOCKET CLIENT
# -----------------------------
async def connect_chat():
    async with websockets.connect(WS_URL) as websocket:
        print(f"✅ Connected to WebSocket at {WS_URL}")

        # Example: send a message
        message_data = {
            "action": "message",
            "receiver_id": "6f1e0446-2681-49a2-8020-4323f4ac1f0f",
            "content": "Hello from Python Parth"
        }
        await websocket.send(json.dumps(message_data))
        print("📤 Message sent!")

        # Example: send typing indicator
        typing_data = {
            "action": "typing",
            "receiver_id": RECEIVER_ID
        }
        await websocket.send(json.dumps(typing_data))
        print("📤 Typing indicator sent!")

        # Listen for incoming messages
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                print("📥 Received:", data)
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ WebSocket connection closed")
                break


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    asyncio.run(connect_chat())
