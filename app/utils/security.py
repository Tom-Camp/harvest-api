from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.utils.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(
        to_encode, settings.USER_SECRET, algorithm=settings.HASH_ALGORITHM
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.USER_SECRET, algorithms=[settings.HASH_ALGORITHM])
