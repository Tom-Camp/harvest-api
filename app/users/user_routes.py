from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import User
from app.users.user_schemas import UserRead, UserUpdate
from app.utils.database import get_db

logger = get_logger(__name__)

user_router = APIRouter(prefix="/users")


@user_router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> UserRead | None:
    """
    A route to return a User object for the current user

    :param current_user: The current user
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: User or None
    """

    user = await UserCRUD.get_user(
        session=session,
        user_id=current_user.id,
    )
    return user


@user_router.get("/", response_model=list[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    """
    A route to return a list of User objects for the current user

    :param skip: The number of users to skip
    :param limit: The number of users to return
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: list[UserRead]; users.user_schemas.UserRead
    """

    users = await UserCRUD.get_users(session, skip=skip, limit=limit)
    return [UserRead.model_validate(user) for user in users]


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    A route to return a User object for the current user

    :param user_id: The UUID of the user
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: UserRead or None
    """

    user = await UserCRUD.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("%s read user" % current_user.username)
    return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    A route to update a User object for the current user

    :param user_id: The UUID of the user
    :param user_update: The UserUpdate object; users.user_schemas.UserUpdate
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: User or None
    """

    user = await UserCRUD.update_user(session, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        event="Update user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            # "target_user_id": existing_user.id,
            # "target_username": existing_user.username,
            "action": "update_user",
            "resource": "user_routes",
        },
    )
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    A route to delete a User object

    :param user_id: The UUID of the user
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    if not await UserCRUD.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        event="Delete user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            # "target_user_id": existing_user.id,
            # "target_username": existing_user.username,
            "action": "delete_user",
            "resource": "user_routes",
        },
    )

    return {"message": f"User {user_id} deleted successfully"}
