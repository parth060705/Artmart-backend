from sqlalchemy.orm import Session  
from pydantic import ValidationError
from typing import Dict
from app.core.auth import get_current_user
from app.database import get_db

# FOR MEASSAGING
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from app.schemas.schemas import (MessageCreate)
from app.crud.crud import create_message

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# FOR CHAT LEVEL ROUTES
chat_router = APIRouter(
    tags=["Chat"],
    dependencies=[Depends(get_current_user)]
)
active_connections: Dict[str, WebSocket] = {}

# -------------------------
#  CHAT ENDPOINTS
# -------------------------

@router.websocket("/ws/{user_id}") # ws://localhost:8000/api/ws/{user_id}, ws://localhost:8000/api/auth/chat/ws/{user_id}
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    db: Session = next(get_db())
    active_connections[user_id] = websocket
    print(f"✅ WebSocket connection established for user: {user_id}")

    try:
        while True:
            try:
                data = await websocket.receive_json()
                print(f"📥 Received from {user_id}: {data}")
                msg = MessageCreate(**data)  # Validate input
            except ValidationError as ve:
                print("❌ Pydantic validation error:", ve)
                await websocket.send_json({
                    "error": "Invalid message format",
                    "details": ve.errors()
                })
                continue
            except Exception as e:
                print(f"❌ JSON receive/parse failed: {e}")
                break

            if msg.action == "message":
                saved_msg = create_message(db, sender_id=user_id, msg=msg)
                payload = {
                    "action": "message",
                    "sender_id": user_id,
                    "content": saved_msg.content,
                    "timestamp": saved_msg.timestamp.isoformat()
                }
                if msg.receiver_id in active_connections:
                    await active_connections[msg.receiver_id].send_json(payload)

            elif msg.action == "typing":
                if msg.receiver_id in active_connections:
                    await active_connections[msg.receiver_id].send_json({
                        "action": "typing",
                        "sender_id": user_id,
                        "is_typing": True
                    })

            elif msg.action == "read":
                create_message.mark_messages_as_read(
                    db, sender_id=msg.receiver_id, receiver_id=user_id
                )
                if msg.receiver_id in active_connections:
                    await active_connections[msg.receiver_id].send_json({
                        "action": "read",
                        "by_user": user_id
                    })

    except WebSocketDisconnect:
        print(f"⚠️ Disconnected: {user_id}")
    except Exception as e:
        print(f"🔥 Unexpected error: {e}")
    finally:
        db.close()
        active_connections.pop(user_id, None)
        print(f"🧹 Cleaned up connection for user: {user_id}")
