import hashlib
from datetime import datetime, timedelta, timezone
from typing import List

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, decode, encode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from zxcvbn_rs_py import zxcvbn

from app.logging import get_logger
from app.users.user_models import User
from app.utils.config import settings
from app.utils.database import get_db

logger = get_logger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.HASH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/"


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        logger.warning("Password mismatch error.")
        return False


def get_password_hash(password: str) -> str:
    return ph.hash(password)


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    statement = select(User).where(User.__table__.c.username == username)
    result = await session.execute(statement)
    user = result.scalars().first()

    if not user:
        logger.warning("Username not found.")
        return None
    if not await verify_password(password, user.hashed_password):
        logger.warning("Incorrect password.")
        return None
    return user


async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    statement = select(User).where(User.__table__.c.username == username)
    result = await session.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def hibp_breach_count(password: str, timeout: float = 10.0) -> int:
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # nosec B324
    prefix, suffix = sha1[:5], sha1[5:]

    headers = {
        "User-Agent": "HarvestAuth/1.0 (password checker))",
        "Add-Padding": "true",
    }

    client = httpx.AsyncClient(timeout=timeout)
    close_client = True
    try:
        resp = await client.get(f"{HIBP_RANGE_URL}{prefix}", headers=headers)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            if not line:
                continue
            sfx, cnt = line.split(":")
            if sfx.upper() == suffix:
                return int(cnt)
        return 0
    finally:
        if close_client:
            await client.aclose()


async def failed_password_messages(reasons: dict) -> List:
    message: List = []
    if reasons.get("pwned_count"):
        message.append(
            "This password appears in known data breaches and can’t be used. Pick a "
            "different, longer passphrase."
        )
    if reasons.get("length", 3) <= 12 or reasons.get("zxcvbn_score", 0) <= 3:
        message.append(
            "This password can’t be used. Use at least 12 characters; a passphrase "
            "of 3–4 uncommon words works well."
        )
    return message


async def assess_password(password: str) -> dict:
    # zxcvbn score 0..4
    score = int(zxcvbn(password).score)
    pwned = await hibp_breach_count(password)
    ok = (len(password) >= 12) and (score >= 3) and (pwned == 0)
    return {
        "ok": ok,
        "length": len(password),
        "zxcvbn_score": score,
        "pwned_count": pwned,
    }
