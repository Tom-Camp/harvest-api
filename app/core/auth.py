import hashlib
from datetime import datetime, timedelta, timezone

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, decode, encode
from sqlmodel import select
from zxcvbn_rs_py import zxcvbn

from app.core.utils.config import settings
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger
from app.models.user_models import User

logger = get_logger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.HASH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/"


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    :param plain_password: The plain-text password to verify
    :param hashed_password: The hashed password to compare to
    :return: bool
    """

    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        logger.warning("Password mismatch error.")
        return False


def get_password_hash(password: str) -> str:
    """
    Return the hashed password from the plain-text password.

    :param password: The password to hash
    :return: The hashed password
    """

    return ph.hash(password)


async def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """
    Create an access token for an API request.

    :param data: The data to encode
    :param expires_delta: The expiration time
    :return: The access token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )

    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the database.

    :param token: The token
    :return: User object
    """

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

    statement = select(User).where(User.username == username)
    session = AsyncSessionLocal()
    result = await session.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get an active user from the database.

    :param current_user: The current user
    :return: The user accessing the route
    """

    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def hibp_breach_count(password: str, timeout: float = 10.0) -> int:
    """
    Check if the password is associated with a known breach

    :param password: The password to check
    :param timeout: The timeout in seconds
    :return: The number of breaches
    """

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


async def failed_password_messages(reasons: dict) -> list:
    """
    Return a list of failed password messages

    :param reasons: The reasons for the failed password messages
    :return: list of messages
    """

    message: list = []
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
    """
    Assess the password complexity using the zxcvbn algorithm. zxcvbn score 0..4

    :param password: The password to check
    :return: dict
    """

    score = int(zxcvbn(password).score)
    pwned = await hibp_breach_count(password)
    ok = (len(password) >= 12) and (score >= 3) and (pwned == 0)
    return {
        "ok": ok,
        "length": len(password),
        "zxcvbn_score": score,
        "pwned_count": pwned,
    }
