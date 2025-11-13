from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal
from app.models.models import AdminAuditLog, User, RoleEnum
from app.core.auth import decode_access_token


class AdminLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Only log /admin routes
        if path.startswith("/api/admin"):
            db: Session = SessionLocal()
            try:
                token = request.headers.get("Authorization")
                if token and token.startswith("Bearer "):
                    token = token.split(" ")[1]
                    decoded = decode_access_token(token)

                    if decoded and decoded.get("username"):
                        user = db.query(User).filter(User.username == decoded["username"]).first()
                        if user and user.role == RoleEnum.admin:
                            log = AdminAuditLog(
                                admin_id=user.id,
                                method=method,
                                path=path,
                                action=f"{method} {path}",
                                description=f"Admin {user.username} called {method} {path}",
                                ip_address=request.headers.get("x-forwarded-for", request.client.host),
                                timestamp=datetime.utcnow()
                            )
                            db.add(log)
                            db.commit()
            except Exception as e:
                print(f"[AdminLoggerMiddleware] Error: {e}")
            finally:
                db.close()

        response = await call_next(request)
        return response
