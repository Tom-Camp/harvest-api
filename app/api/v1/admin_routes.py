from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth.auth import get_current_user
from app.core.auth.scopes_manager import ScopesManager
from app.core.utils.database import AsyncSessionLocal, get_db
from app.logging import get_logger, log_handler
from app.models.user_models import Role
from app.schemas.auth_schemas import TokenData
from app.schemas.role_schemas import RoleRequest
from app.services.user_service import UserService

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin")


def get_admin_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


@admin_router.post("/role/assign")
async def assign_role(
    role_request: RoleRequest,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:ar"])],
    service: UserService = Depends(get_admin_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scope operation: Assign a role to user.

    :param role_request: Role to assign
    :param current_user: The user currently accessing the route
    :param service: services.user_service.UserService
    :param session: AsyncSession; sqlachemy.ext.asyncio.AsyncSession
    :return: dict
    """

    user = await service.get_user(user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    statement = select(Role).where(Role.name == role_request.role_name)
    result = await session.execute(statement)
    role = result.scalars().first()
    if role is None:
        raise HTTPException(status_code=404, detail="Not found")

    user = await service.add_user_role(
        user_id=user.id,
        role=role,
    )
    log_handler.log_security_event(
        "Role assigned to user",
        severity="medium",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": role_request.user_id,
            "target_username": user.username,
            "role_name": role_request.role_name,
            "action": "assign_role",
            "resource": "admin_routes",
        },
    )

    return {
        "message": f"Role '{role_request.role_name}' assigned to user '{user.username}'"
    }


@admin_router.post("/role/remove")
async def remove_role(
    role_request: RoleRequest,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:rr"])],
    service: UserService = Depends(get_admin_service),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scope operation: Remove a role from a user.

    :param role_request: Role to remove
    :param current_user: The user currently accessing the route
    :param service: services.user_service.UserService
    :param session: AsyncSession; sqlachemy.ext.asyncio.AsyncSession
    :return: dict
    """

    user = await service.get_user(user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    statement = select(Role).where(Role.name == role_request.role_name)
    result = await session.execute(statement)
    role = result.scalars().first()
    if role is None:
        raise HTTPException(status_code=404, detail="Not found")

    if role not in user.roles:
        raise HTTPException(
            status_code=400, detail="User does not have the specified role"
        )

    user = await service.remove_user_role(
        user_id=user.id,
        role=role,
    )

    log_handler.log_security_event(
        "Role removed from user",
        severity="medium",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": role_request.user_id,
            "target_username": user.username,
            "role_name": role_request.role_name,
            "action": "remove_role",
            "resource": "admin_routes",
        },
    )

    return {
        "message": f"Role '{role_request.role_name}' removed from user '{user.username}'"
    }


@admin_router.get("/role/permissions/{user_id}")
async def check_permission(
    user_id: UUID,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:cp"])],
    service: UserService = Depends(get_admin_service),
) -> list:
    """
    Scope operation: Check user permissions.

    :param user_id: user's unique ID
    :param current_user: The user accessing the route
    :param service: services.user_service.UserService
    :return: dict
    """

    user = await service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    scopes = ScopesManager.get_scopes_for_roles(roles=user.roles)
    permissions = ScopesManager.get_role_permission(scopes=scopes)

    log_handler.log_security_event(
        "Permission check",
        severity="low",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": user_id,
            "target_username": user.username,
            "action": "check_permission",
            "resource": "admin_routes",
        },
    )

    return permissions


@admin_router.get("/roles/{user_id}", response_model=list[str])
async def get_user_roles(
    user_id: UUID,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:gr"])],
    service: UserService = Depends(get_admin_service),
) -> list[str]:
    """
    Scopes operation: Get a user's roles.

    :param user_id: The UUID of the user whose roles to return
    :param current_user: the User accessing the route
    :param service: services.user_service.UserService
    :return: list
    """

    user = await service.get_user_with_roles(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_handler.log_security_event(
        "List user roles",
        severity="low",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": user_id,
            "action": "get_user_roles",
            "resource": "admin_routes",
        },
    )
    return [role.name for role in user.roles]
