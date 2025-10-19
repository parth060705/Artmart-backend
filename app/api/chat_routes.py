# from fastapi import WebSocket, WebSocketDisconnect, APIRouter
# from typing import Dict
# from app.crud.user_crud import get_user_by_username
# # from app.crud.chat_crud import create_message
# from app.database import get_db
# from app.schemas.chat_schemas import MessageCreate
# from app.core.auth import decode_access_token
# from sqlalchemy.orm import Session
# from datetime import datetime
# from fastapi import Depends
# from fastapi import APIRouter
# from sqlalchemy.orm import Session
# from typing import List
# from app.crud.chat_crud import get_messages_between, create_message, mark_messages_as_read
# # from app.crud import chat_crud

# from app.schemas.chat_schemas import MessageOut
# from app.core.auth import get_current_user
# from app.database import get_db
# import traceback

# # -------------------------
# # ROUTER & CONNECTIONS
# # -------------------------
# chat_router = APIRouter(tags=["Chat"])
# active_connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket

# # -------------------------
# # AUTH HELPERS
# # -------------------------
# async def get_current_user_ws(websocket: WebSocket) -> tuple:
#     """Authenticate user from WebSocket query param token."""
#     token = websocket.query_params.get("token")
#     if not token:
#         await websocket.close(code=1008)
#         return None, None

#     username = decode_access_token(token)
#     if not username:
#         await websocket.close(code=1008)
#         return None, None

#     db: Session = next(get_db())
#     user = get_user_by_username(db, username)
#     if not user:
#         await websocket.close(code=1008)
#         return None, None

#     return user, db

# # -------------------------
# # WEBSOCKET ENDPOINT
# # -------------------------
# @chat_router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     user, db = await get_current_user_ws(websocket)
#     if not user:
#         return

#     await websocket.accept()
#     user_id = str(user.id)
#     active_connections[user_id] = websocket
#     print(f"✅ WebSocket connected for user: {user.username} ({user_id})")

#     try:
#         while True:
#             try:
#                 data = await websocket.receive_json()
#             except Exception as e:
#                 print("❌ Error receiving JSON:", e)
#                 await websocket.send_json({"error": "Invalid JSON"})
#                 continue

#             action = data.get("action")

#             # -------------------------
#             # MESSAGE ACTION
#             # -------------------------
#             if action == "message":
#                 try:
#                     msg = MessageCreate(**data)
#                 except Exception as e:
#                     print("❌ Invalid message format:", e)
#                     traceback.print_exc()
#                     await websocket.send_json({"error": "Invalid message format from backend"})
#                     continue

#                 try:
#                     saved_msg = create_message(db, sender_id=user_id, msg=msg)
#                 except Exception as e:
#                     print("❌ Error saving message:", e)
#                     traceback.print_exc()
#                     await websocket.send_json({"error": "Failed to save message"})
#                     continue

#                 payload = {
#                     "action": "message",
#                     "sender_id": user_id,
#                     "receiver_id": msg.receiver_id,
#                     "content": saved_msg.content,
#                     "timestamp": saved_msg.timestamp.isoformat() if saved_msg.timestamp else datetime.utcnow().isoformat()
#                 }

#                 receiver_ws = active_connections.get(msg.receiver_id)
#                 if receiver_ws:
#                     await receiver_ws.send_json(payload)

#             # -------------------------
#             # TYPING ACTION
#             # -------------------------
#             elif action == "typing":
#                 receiver_ws = active_connections.get(data.get("receiver_id"))
#                 if receiver_ws:
#                     await receiver_ws.send_json({
#                         "action": "typing",
#                         "sender_id": data.get("sender_id"),
#                         "is_typing": True
#                     })

#             # -------------------------
#             # READ ACTION
#             # -------------------------
#             elif action == "read":
#                 try:
#                     mark_messages_as_read(db, sender_id=data.get("receiver_id"), receiver_id=user_id)
#                 except Exception as e:
#                     print(f"❌ Error marking messages as read: {e}")
#                     traceback.print_exc()

#                 receiver_ws = active_connections.get(data.get("receiver_id"))
#                 if receiver_ws:
#                     await receiver_ws.send_json({
#                         "action": "read",
#                         "by_user": user_id
#                     })

#             # -------------------------
#             # OTHER ACTIONS (e.g., presence)
#             # -------------------------
#             else:
#                 receiver_ws = active_connections.get(data.get("receiver_id"))
#                 if receiver_ws:
#                     await receiver_ws.send_json(data)
#                 else:
#                     await websocket.send_json({"error": "Unknown action"})

#     except WebSocketDisconnect:
#         print(f"⚠️ User disconnected: {user_id}")

#     finally:
#         active_connections.pop(user_id, None)
#         db.close()
#         print(f"🧹 Cleaned up connection for user: {user_id}")


# # -------------------------
# # CHAT HISTORY ENDPOINT
# # ------------------------

# @chat_router.get("/history/{other_user_id}", response_model=List[MessageOut])
# def get_chat_history(
#     other_user_id: str,
#     current_user=Depends(get_current_user),
#     db: Session = Depends(get_db),
#     limit: int = 50
# ):
#     messages = get_messages_between(db, current_user.id, other_user_id, limit)
#     return messages        

# # -------------------------
# # CHAT LIST ENDPOINT
# # ------------------------

# @chat_router.get("/chatslist")
# def get_user_chat_list(
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     from app.crud.chat_crud import get_chat_users
#     chat_users = get_chat_users(db, current_user.id)
#     return chat_users

# ------------------------- WebSocket & API -------------------------
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from typing import Dict, List
from app.crud.user_crud import get_user_by_username
from app.crud.chat_crud import get_messages_between, create_message, mark_messages_as_read
from app.database import get_db
from app.schemas.chat_schemas import MessageCreate, MessageOut
from app.core.auth import decode_access_token, get_current_user
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

chat_router = APIRouter(tags=["Chat"])
active_connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket

# -------------------------
# Authenticate WebSocket user
# -------------------------
async def get_current_user_ws(websocket: WebSocket) -> tuple:
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
# WebSocket endpoint
# -------------------------
@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user, db = await get_current_user_ws(websocket)
    if not user:
        return

    await websocket.accept()
    user_id = str(user.id)
    active_connections[user_id] = websocket
    print(f"✅ WebSocket connected for user: {user.username} ({user_id})")

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception as e:
                print("❌ Error receiving JSON:", e)
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            action = data.get("action")

            # -------------------------
            # MESSAGE
            # -------------------------
            if action == "message":
                try:
                    msg = MessageCreate(**data)
                except Exception as e:
                    print("❌ Invalid message format:", e)
                    traceback.print_exc()
                    await websocket.send_json({"error": "Invalid message format"})
                    continue

                try:
                    saved_msg = create_message(db, sender_id=user_id, msg=msg)
                except Exception as e:
                    print("❌ Error saving message:", e)
                    traceback.print_exc()
                    await websocket.send_json({"error": "Failed to save message"})
                    continue

                payload = {
                    "action": "message",
                    "sender_id": user_id,
                    "receiver_id": msg.receiver_id,
                    "content": saved_msg.content,
                    "timestamp": saved_msg.timestamp.isoformat() if saved_msg.timestamp else datetime.utcnow().isoformat()
                }

                # Send to receiver if online
                receiver_ws = active_connections.get(msg.receiver_id)
                if receiver_ws:
                    await receiver_ws.send_json(payload)

            # -------------------------
            # TYPING / PRESENCE / PING / READ
            # -------------------------
            elif action in ["typing", "presence", "ping", "read"]:
                receiver_id = data.get("receiver_id")
                if action == "read":
                    try:
                        mark_messages_as_read(db, sender_id=receiver_id, receiver_id=user_id)
                    except Exception as e:
                        print(f"❌ Error marking messages as read: {e}")
                        traceback.print_exc()

                # Broadcast to receiver if online
                receiver_ws = active_connections.get(receiver_id)
                if receiver_ws:
                    await receiver_ws.send_json(data)

            else:
                await websocket.send_json({"error": "Unknown action"})

    except WebSocketDisconnect:
        print(f"⚠️ User disconnected: {user_id}")

    finally:
        active_connections.pop(user_id, None)
        db.close()
        print(f"🧹 Cleaned up connection for user: {user_id}")

# -------------------------
# Chat history endpoint
# -------------------------
@chat_router.get("/history/{other_user_id}", response_model=List[MessageOut])
def get_chat_history(
    other_user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    messages = get_messages_between(db, current_user.id, other_user_id, limit)
    return messages

# -------------------------
# Chat list endpoint
# -------------------------
@chat_router.get("/chatslist")
def get_user_chat_list(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    from app.crud.chat_crud import get_chat_users
    return get_chat_users(db, current_user.id)
