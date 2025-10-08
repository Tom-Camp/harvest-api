from jwt import InvalidTokenError, decode
from sqlmodel import select
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)

from app.core.utils.config import settings
from app.core.utils.database import AsyncSessionLocal
from app.models.user_models import User

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.HASH_ALGORITHM


class JWTAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        # Accept only HTTP/WebSocket
        auth_header = conn.headers.get("Authorization")
        if not auth_header:
            return

        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return

        # Validate and decode JWT
        try:
            payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except InvalidTokenError as exc:
            raise AuthenticationError(f"Invalid token: {exc}")

        username = payload.get("sub")
        if not username:
            raise AuthenticationError("Missing subject")

        # Load user from DB
        session = AsyncSessionLocal()
        try:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalars().first()
        finally:
            await session.close()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Attach scopes if desired; here only "authenticated"
        return AuthCredentials(["authenticated"]), SimpleUser(user.id)
