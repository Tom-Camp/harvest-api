import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import AsyncCasbinManager
from app.casbin.permissions import RequireUserRead, RequireUserWrite
from app.users.user_models import User
from app.users.user_schemas import UserRead, UserReadWithRoles, UserUpdate
from app.users.users_crud import UserCRUD
from app.utils.database import get_session
from app.utils.dependencies import get_casbin_manager

user_router = APIRouter(prefix="/users")


@user_router.get("/me", response_model=UserReadWithRoles)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    user = await UserCRUD.get_user_with_roles(
        session=session,
        user_id=current_user.id,
    )
    return user


@user_router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    users = await UserCRUD.get_users(session, skip=skip, limit=limit)
    logging.info("%s listed all users" % current_user.username)
    return users


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    user = UserCRUD.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logging.info("%s read user" % current_user.username)
    return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    if str(user_id) != str(current_user.id):
        user_identifier = f"user:{current_user.username}"
        if not casbin_manager.check_permission(user_identifier, "user", "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

    user = UserCRUD.update_user(session, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireUserWrite),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    if not UserCRUD.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    user = await UserCRUD.get_user(session, user_id)
    if user:
        user_identifier = f"user:{user.username}"
        roles = await casbin_manager.get_roles_for_user(user_identifier)
        for role in roles:
            await casbin_manager.remove_role_for_user(user_identifier, role)

    logging.info("%s deleted user %s" % current_user.username, user_id)
    return {"message": "User deleted successfully"}
