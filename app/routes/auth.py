import uuid
from fastapi import Depends, HTTPException
from app.db.enums import UserRole


from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from app.db.create_db import get_user_db
from app.db.models import User
from app.core.email import send_reset_password_email, send_verification_email
from app.core.config import settings
from typing import Optional
from fastapi import Request

SECRET = settings.JWT_SECRET


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request=None):
        await self.request_verify(user, request)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print("🔥 on_after_request_verify", flush=True)
        await send_verification_email(email=user.email, token=token)

    async def on_after_forgot_password(self, user: User, token: str, request=None):
        await send_reset_password_email(user.email, token)

    async def on_after_request_verify(self, user: User, token: str, request=None):
        await send_verification_email(user.email, token)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/login")


def get_jwt_strategy():
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager, auth_backends=[auth_backend]
)

current_active_user = fastapi_users.current_user(active=True)


async def require_admin(
    user: User = Depends(current_active_user),
) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return user
