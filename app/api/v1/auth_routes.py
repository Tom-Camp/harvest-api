from datetime import timedelta

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    assess_password,
    create_access_token,
    failed_password_messages,
    verify_password,
)
from app.core.helpers.garden_helpers import add_default_garden
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.user_models import User
from app.schemas.auth_schemas import Token, UserLogin
from app.schemas.user_schemas import UserCreate, UserRead
from app.services.user_service import UserService

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/auth")


def get_user_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    user_login: UserLogin,
    service: UserService = Depends(get_user_service),
) -> dict:
    """
    Login route to obtain access token.

    :param request: Request
    :param user_login: UserLogin; auth.auth_schema.UserLogin
    :param service: UserService; services.user_service.UserService
    """

    valid_pw: bool = False
    user = await service.get_user_by_username(username=user_login.username)
    if user:
        valid_pw = await verify_password(user_login.password, user.hashed_password)
    if not user or not valid_pw:
        log_handler.log_security_event(
            "user_login_failure",
            severity="moderate",
            context={
                "event_type": "authentication",
                "username": user_login.username,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "action": "login_for_access_token",
                "resource": "auth_routes",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    log_handler.log_security_event(
        event="user_login_success",
        severity="low",
        context={
            "event_type": "authentication",
            "username": user.username,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user.id,
            "action": "login_for_access_token",
            "resource": "auth_routes",
        },
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", response_model=UserRead)
async def register(
    request: Request,
    user: UserCreate,
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
    service: UserService = Depends(get_user_service),
) -> User:
    """
    User Registration route.

    :param request: Request
    :param user: UserCreate object; users.user_schemas.UserCreate
    :param enforcer: Casbin AsyncEnforcer
    :param service: UserService; services.user_service.UserService
    """

    if username := await service.get_user_by_username(username=user.username):
        logger.info("Username %s already taken" % username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if email := await service.get_user_by_email(email=user.email):
        logger.warning("Email %s already taken" % email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    pw_is_valid = await assess_password(password=user.password)
    if not pw_is_valid.get("ok"):
        log_handler.log_security_event(
            "insufficient_password_complexity",
            severity="low",
            context={
                "event_type": "authentication",
                "username": user.username,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "ok": pw_is_valid.get("ok"),
                "length": pw_is_valid.get("length"),
                "zxcvbn_score": pw_is_valid.get("zxcvbn_score"),
                "pwned_count": pw_is_valid.get("pwned_count"),
                "action": "register",
                "resource": "auth_routes",
            },
        )
        response_message = await failed_password_messages(pw_is_valid)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=response_message,
        )

    new_user = await service.create_user(user)

    await enforcer.add_role_for_user(casbin_subject(new_user.id), "authenticated")

    log_handler.log_security_event(
        "user_register_success",
        severity="low",
        context={
            "event_type": "authentication",
            "username": user.username,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user_id": new_user.id,
            "action": "register",
            "resource": "auth_routes",
        },
    )

    await add_default_garden(user=new_user)

    return new_user
