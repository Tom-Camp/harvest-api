from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jwt import InvalidTokenError, decode, encode
from pydantic import ValidationError

from app.core.auth.auth_helpers import oauth2_scheme, verify_password
from app.core.auth.scopes_manager import ScopesManager
from app.core.utils.config import settings
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger
from app.models.user_models import User
from app.schemas.auth_schemas import TokenData
from app.services.user_service import UserService

logger = get_logger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.HASH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_current_user_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


async def authenticate_user(
    username: str, password: str, service: UserService
) -> User | None:
    """
    Authenticate a user using the username and password.

    :param username: The unique username
    :param password: The password
    :param service: UserService; services.user_service.UserService
    :return: User or None
    """

    user = await service.get_user_by_username(username=username)
    if not user:
        logger.warning("Username not found.")
        return None

    if not await verify_password(password, user.hashed_password):
        logger.warning("Incorrect password.")
        return None

    return user


async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create an access token for an API request.

    :param data: The data to encode
    :param expires_delta: The expiration time
    :return: The access token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    service: UserService = Depends(get_current_user_service),
) -> TokenData:
    """
    Get the current user from the database.

    :param security_scopes: SecurityScopes;
    :param token: The token
    :param service: UserService; services.user_service.UserService
    :return: User object
    """

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

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
        token_scopes: list[str] = payload.get("scope", "").split()
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    user = await service.get_user_by_username(username=username)
    if user is None:
        raise credentials_exception

    if not ScopesManager.has_any_scope(
        user_scopes=token_scopes, required_scopes=security_scopes.scopes
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return TokenData(
        id=user.id,
        username=user.username,
        scopes=token_scopes,
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get an active user from the database.

    :param current_user: The current user
    :return: The active User object
    """

    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
