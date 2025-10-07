from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.core.auth import get_current_active_user
from app.core.helpers.user_helpers import user_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.user_models import User
from app.schemas.user_schemas import UserRead, UserUpdate
from app.services.user_service import UserService

logger = get_logger(__name__)

user_router = APIRouter(prefix="/users")


def get_user_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


@user_router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> UserRead | None:
    """
    A route to return a User object for the current user

    :param current_user: The current user
    :param service: UserService; services.user_service.UserService
    :param enforcer: The Casbin AsyncEnforcer
    :return: User or None
    """

    _ = await user_check_access(
        service=service,
        user_id=current_user.id,
        current_user=current_user,
        enforcer=enforcer,
        action="read",
    )

    user = await service.get_user(user_id=current_user.id)
    if user:
        await enforcer.add_role_for_user(
            user=casbin_subject(user.id), role="authenticated"
        )
    return user


@user_router.get("/", response_model=list[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """
    A route to return a list of User objects for the current user

    :param skip: The number of users to skip
    :param limit: The number of users to return
    :param service: UserService; services.user_service.UserService
    :return: list[UserRead]; users.user_schemas.UserRead
    """

    users = await service.get_users(skip=skip, limit=limit)
    return [UserRead.model_validate(user) for user in users]


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> User:
    """
    A route to return a User object for the current user

    :param user_id: The UUID of the user
    :param service: UserService; services.user_service.UserService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: UserRead or None
    """

    _ = await user_check_access(
        service=service,
        user_id=user_id,
        current_user=current_user,
        enforcer=enforcer,
        action="read",
    )

    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("%s read user" % current_user.username)
    return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> User:
    """
    A route to update a User object for the current user

    :param user_id: The UUID of the user
    :param user_update: The UserUpdate object; users.user_schemas.UserUpdate
    :param service: UserService; services.user_service.UserService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: User or None
    """

    existing_user = await user_check_access(
        service=service,
        user_id=user_id,
        current_user=current_user,
        enforcer=enforcer,
        action="update",
    )

    user = await service.update_user(user_id=user_id, user_update=user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        event="Update user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": existing_user.id,
            "target_username": existing_user.username,
            "action": "update_user",
            "resource": "user_routes",
        },
    )
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a User object

    :param user_id: The UUID of the user
    :param service: UserService; services.user_service.UserService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    existing_user = await user_check_access(
        service=service,
        user_id=user_id,
        current_user=current_user,
        enforcer=enforcer,
        action="delete",
    )

    if not await service.delete_user(user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")

    await enforcer.delete_user(casbin_subject(user_id))

    log_handler.log_security_event(
        event="Delete user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": existing_user.id,
            "target_username": existing_user.username,
            "action": "delete_user",
            "resource": "user_routes",
        },
    )

    return {"message": f"User {existing_user.username} deleted successfully"}
