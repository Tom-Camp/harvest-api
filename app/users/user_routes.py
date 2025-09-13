from typing import List, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import casbin_manager
from app.casbin.casbin_helpers import casbin_object, casbin_subject
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
) -> User | None:
    user = await UserCRUD.get_user(
        session=session,
        user_id=current_user.id,
    )
    return user


@user_router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> Sequence:
    users = await UserCRUD.get_users(session, skip=skip, limit=limit)
    return users


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    allowed = await casbin_manager.enforce(
        casbin_subject(current_user.id), casbin_object("u", user_id), "read"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

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
    allowed = await casbin_manager.enforce(
        casbin_subject(current_user.id), casbin_object("u", user_id), "update"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = await UserCRUD.update_user(session, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    allowed = await casbin_manager.enforce(
        casbin_subject(current_user.id), casbin_object("u", user_id), "update"
    )
    user = await UserCRUD.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not UserCRUD.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    await casbin_manager.delete_roles_for_user(casbin_subject(user_id))

    log_handler.log_security_event(
        event="User deleted",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": user.id,
            "target_username": user.username,
            "action": "user_delete",
        },
    )
    return {"message": f"User {user.username} deleted successfully"}
