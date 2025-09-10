import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_sessionmaker

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
    sessionmaker: async_sessionmaker = Depends(get_session),
):
    async with sessionmaker() as session:
        user = await UserCRUD.get_user_with_roles(
            session=session,
            user_id=current_user.id,
        )
        return user


@user_router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    sessionmaker: async_sessionmaker = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    async with sessionmaker() as session:
        users = await UserCRUD.get_users(session, skip=skip, limit=limit)
        logging.info("%s listed all users" % current_user.username)
        return users


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    sessionmaker: async_sessionmaker = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    async with sessionmaker() as session:
        user = UserCRUD.get_user(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logging.info("%s read user" % current_user.username)
        return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    sessionmaker: async_sessionmaker = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    async with sessionmaker() as session:
        if str(user_id) != str(current_user.id):
            allowed = await manager.enforce(
                sub=f"user:{current_user.username}",
                obj="user",
                act="write",
            )
            if not allowed:
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
    sessionmaker: async_sessionmaker = Depends(get_session),
    current_user: User = Depends(RequireUserWrite),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    async with sessionmaker() as session:
        if not UserCRUD.delete_user(session, user_id):
            raise HTTPException(status_code=404, detail="User not found")

        user = await UserCRUD.get_user(session, user_id)
        if user:
            user_identifier = f"user:{user.username}"
            roles = await manager.get_roles_for_user(user_identifier)
            for role in roles:
                await manager.delete_role_for_user(user_identifier, role)

        logging.info("%s deleted user %s" % current_user.username, user_id)
        return {"message": "User deleted successfully"}
