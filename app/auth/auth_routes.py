from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    assess_password,
    authenticate_user,
    create_access_token,
    failed_password_messages,
)
from app.auth.auth_schemas import Token, UserLogin
from app.beds.bed_crud import BedCRUD
from app.beds.bed_schemas import BedCreate
from app.core.auth.scopes_manager import ScopesManager
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_schemas import GardenCreate
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import User
from app.users.user_schemas import UserCreate, UserRead
from app.utils.database import get_db

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/auth")


async def add_default_bed(session: AsyncSession, garden_id: UUID):
    """
    Add a default bed to the default garden for a new User.

    :param session: SQLAlchemy asyncio AsyncSession
    :param garden_id: The garden UUID
    """

    bed = BedCreate(
        name="Default bed",
        description="A garden bed",
        garden_id=garden_id,
    )
    await BedCRUD.create_bed(bed=bed, session=session)


async def add_default_garden(user: User, session: AsyncSession):
    """
    Add a default garden for a new User.

    :param user: The new User object
    :param session: SQLAlchemy asyncio AsyncSession
    """

    garden = GardenCreate(
        name="Default garden",
        description="Garden added when user created",
        location="Lebanon, Kansas",
        is_private=False,
    )
    default_garden = await GardenCRUD.create_garden(
        garden=garden, session=session, user=user
    )
    if default_garden:
        await add_default_bed(session=session, garden_id=default_garden.id)
        await session.refresh(default_garden, ["beds"])

        log_handler.log_security_event(
            "add_default_garden",
            severity="moderate",
            context={
                "event_type": "registration",
                "user_name": user.username,
                "user_id": user.id,
                "garden_id": default_garden.id,
                "resource": "auth_routes",
            },
        )
    else:
        log_handler.log_security_event(
            "default_garden_create_failed",
            severity="moderate",
            context={
                "event_type": "registration",
                "user_name": user.username,
                "user_id": user.id,
                "action": "default_garden_failed",
                "resource": "auth_routes",
            },
        )
    return default_garden


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    user_login: UserLogin,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Login route to obtain access token.

    :param request: Request
    :param form_data: OAuth2PasswordRequestForm containing username and password
    :param session: SQLAlchemy asyncio AsyncSession
    """

    user = await authenticate_user(session, user_login.username, user_login.password)
    if not user:
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
    user_scopes = ScopesManager.get_scopes_for_role(user.role)
    token = await create_access_token(
        data={"sub": user.username, "scope": " ".join(user_scopes)},
        expires_delta=access_token_expires,
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
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/register", response_model=UserRead)
async def register(
    request: Request,
    user: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    User Registration route.

    :param request: Request
    :param user: UserCreate object; users.user_schemas.UserCreate
    :param session: SQLAlchemy asyncio AsyncSession
    """

    if username := await UserCRUD.get_user_by_username(session, user.username):
        logger.info("Username %s already taken" % username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if email := await UserCRUD.get_user_by_email(session, user.email):
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

    new_user = await UserCRUD.create_user(session, user)

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

    await add_default_garden(user=new_user, session=session)

    return new_user
