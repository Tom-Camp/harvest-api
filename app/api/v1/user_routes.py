from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security

from app.core.auth.auth import get_current_user
from app.core.auth.scopes_manager import ScopesManager
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.schemas.auth_schemas import TokenData
from app.schemas.user_schemas import UserRead, UserUpdate
from app.services.user_service import UserService

logger = get_logger(__name__)

user_router = APIRouter(prefix="/users")


def get_user_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


@user_router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["us:re", "us:re:own"])
    ],
    service: UserService = Depends(get_user_service),
) -> UserRead | None:
    """
    A route to return a User object for the current user

    :param current_user: The current user
    :param service: UserService; services.user_service.UserService
    :return: User or None
    """

    user = await service.get_user(user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="us:re"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="us:re:own",
        user_id=current_user.id,
        entity_owner=user.id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

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
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["us:re", "us:re:own"])
    ],
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    A route to return a User object for the current user

    :param user_id: The UUID of the user=
    :param current_user: The current user
    :param service: UserService; services.user_service.UserService
    :return: UserRead or None
    """

    user = await service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="us:re"
    )
    logger.info(f"ANY: {access_any}")
    logger.info(f"{current_user.scopes}")
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="us:re:own",
        user_id=current_user.id,
        entity_owner=user.id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["us:up", "us:up:own"])
    ],
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """
    A route to update a User object for the current user

    :param user_id: The UUID of the user
    :param user_update: The UserUpdate object; schemas.user_schemas.UserUpdate
    :param current_user: The User accessing the route
    :param service: UserService; services.user_service.UserService
    :return: User or None
    """

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="us:up"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="us:up:own",
        user_id=current_user.id,
        entity_owner=user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = await service.update_user(user_id=user_id, user_update=user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        event="Update user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": user_id,
            "target_username": user.username,
            "action": "update_user",
            "resource": "user_routes",
        },
    )
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: Annotated[
        TokenData, Security(get_current_user, scopes=["us:de", "us:de:own"])
    ],
    service: UserService = Depends(get_user_service),
) -> dict:
    """
    A route to delete a User object

    :param user_id: The UUID of the user
    :param current_user: The current user
    :param service: UserService; services.user_service.UserService
    :return: dict
    """

    user = await service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope="us:de"
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope="us:de:own",
        user_id=current_user.id,
        entity_owner=user_id,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await service.delete_user(user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        event="Delete user",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": user_id,
            "action": "delete_user",
            "resource": "user_routes",
        },
    )

    return {"message": f"User {user_id} deleted successfully"}
