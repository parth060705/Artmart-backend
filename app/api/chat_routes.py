from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict
from app.crud.crud import get_user_by_username
from app.crud.chat_crud import create_message
from app.database import get_db
from app.schemas.chat_schemas import MessageCreate
from app.core.auth import decode_access_token
from sqlalchemy.orm import Session
from datetime import datetime

# -------------------------
# ROUTER & CONNECTIONS
# -------------------------
chat_router = APIRouter(tags=["Chat"])
active_connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket


# -------------------------
# AUTH HELPERS
# -------------------------
async def get_current_user_ws(websocket: WebSocket) -> tuple:
    """Authenticate user from WebSocket query param token."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return None, None

    username = decode_access_token(token)
    if not username:
        await websocket.close(code=1008)
        return None, None

    db: Session = next(get_db())
    user = get_user_by_username(db, username)
    if not user:
        await websocket.close(code=1008)
        return None, None

    return user, db


# -------------------------
# CHAT ENDPOINT
# -------------------------
@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Authenticate user first
    user, db = await get_current_user_ws(websocket)
    if not user:
        return

    await websocket.accept()  # Accept only if token is valid
    user_id = str(user.id)
    active_connections[user_id] = websocket
    print(f"✅ WebSocket connected for user: {user.username} ({user_id})")

    try:
        while True:
            try:
                data = await websocket.receive_json()
                msg = MessageCreate(**data)
            except Exception:
                await websocket.send_json({"error": "Invalid message format"})
                continue

            # -------------------------
            # MESSAGE ACTION
            # -------------------------
            if msg.action == "message":
                try:
                    saved_msg = create_message(db, sender_id=user_id, msg=msg)
                except Exception as e:
                    print(f"❌ Error saving message: {e}")
                    await websocket.send_json({"error": "Failed to save message"})
                    continue

                payload = {
                    "action": "message",
                    "sender_id": user_id,
                    "receiver_id": msg.receiver_id,
                    "content": saved_msg.content,
                    "timestamp": saved_msg.timestamp.isoformat()
                }

                # Send to receiver if online
                receiver_ws = active_connections.get(msg.receiver_id)
                if receiver_ws:
                    await receiver_ws.send_json(payload)

            # -------------------------
            # TYPING ACTION
            # -------------------------
            elif msg.action == "typing":
                receiver_ws = active_connections.get(msg.receiver_id)
                if receiver_ws:
                    await receiver_ws.send_json({
                        "action": "typing",
                        "sender_id": user_id,
                        "is_typing": True
                    })

            # -------------------------
            # READ ACTION
            # -------------------------
            elif msg.action == "read":
                try:
                    create_message.mark_messages_as_read(
                        db, sender_id=msg.receiver_id, receiver_id=user_id
                    )
                except Exception as e:
                    print(f"❌ Error marking messages as read: {e}")

                receiver_ws = active_connections.get(msg.receiver_id)
                if receiver_ws:
                    await receiver_ws.send_json({
                        "action": "read",
                        "by_user": user_id
                    })

            else:
                await websocket.send_json({"error": "Unknown action"})

    except WebSocketDisconnect:
        print(f"⚠️ User disconnected: {user_id}")

    finally:
        # Cleanup
        active_connections.pop(user_id, None)
        db.close()
        print(f"🧹 Cleaned up connection for user: {user_id}")
