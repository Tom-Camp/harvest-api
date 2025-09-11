from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
)
from app.auth.auth_schemas import Token
from app.casbin.casbin_config import AsyncCasbinManager
from app.logging import get_logger
from app.users.user_schemas import UserCreate, UserRead
from app.users.users_crud import UserCRUD
from app.utils.database import get_db
from app.utils.dependencies import get_casbin_manager

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        logger.warning("Failed login attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register", response_model=UserRead)
async def register(
    user: UserCreate,
    session: AsyncSession = Depends(get_db),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    if username := await UserCRUD.get_user_by_username(session, user.username):
        logger.info("Username %s already taken" % username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if email := await UserCRUD.get_user_by_email(session, user.email):
        logger.info("Email %s already taken" % email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    db_user = await UserCRUD.create_user(session, user)

    user_identifier = f"user:{db_user.username}"
    await casbin_manager.add_role_for_user(user_identifier, "user")

    return db_user
