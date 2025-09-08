import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.casbin.permissions import RequireAdmin, RequireUserRead
from app.users.role_crud import RoleCRUD
from app.users.user_models import User
from app.users.user_schemas import RoleCreate, RoleRead
from app.utils.database import get_session

role_router = APIRouter(prefix="/users")


@role_router.post("/", response_model=RoleRead)
async def create_role(
    role: RoleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireAdmin),
):
    existing_role = await RoleCRUD.get_role_by_name(session, role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists"
        )
    logging.info("%s created role %s" % current_user.username, role.name)
    return await RoleCRUD.create_role(session, role)


@role_router.get("/", response_model=List[RoleRead])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    logging.info("%s listed all roles" % current_user.username)
    return await RoleCRUD.get_roles(session, skip=skip, limit=limit)


@role_router.get("/{role_id}", response_model=RoleRead)
async def read_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireUserRead),
):
    role = await RoleCRUD.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    logging.info("%s read role %s" % current_user.username, role.name)
    return role
