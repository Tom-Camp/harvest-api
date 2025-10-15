from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.permission_schemas import PermissionCheck, RoleRequest
from app.auth.auth import get_current_user
from app.auth.auth_schemas import TokenData
from app.core.auth.scopes_manager import ScopesManager
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import Role
from app.users.user_schemas import UserUpdateRole
from app.utils.database import get_db

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin")


@admin_router.post("/assign-role")
async def assign_role(
    role_request: RoleRequest,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:ar"])],
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scope operation: Assign a role to user.

    :param role_request: Role to assign
    :param current_user: The user currently accessing the route
    :param session: SQLAlchemy asyncio session
    """

    user = await UserCRUD.get_user(session=session, user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user = await UserCRUD.update_user_role(
        session=session,
        user_id=user.id,
        role=UserUpdateRole(role=Role(role_request.role_name)),
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
        "message": f"Role '{role_request.role_name}' assigned to user '{role_request.username}'"
    }


@admin_router.post("/remove-role")
async def remove_role(
    role_request: RoleRequest,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:rr"])],
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scope operation: Remove a role from a user.

    :param role_request: Role to remove
    :param current_user: The user currently accessing the route
    :param session: SQLAlchemy asyncio session
    """

    user = await UserCRUD.get_user(session=session, user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user = await UserCRUD.update_user_role(
        session=session,
        user_id=user.id,
        role=UserUpdateRole(role=Role.AUTHENTICATED),
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
        "message": f"Role '{role_request.role_name}' removed from user '{role_request.username}'"
    }


@admin_router.post("/check-permission")
async def check_permission(
    permission_request: PermissionCheck,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:cp"])],
    session: AsyncSession = Depends(get_db),
) -> list:
    """
    Scope operation: Check user permissions.

    :param permission_request: PermissionCheck object containing the User ID, permission, and action
    :param current_user: Current user User object
    :param session: SQLAlchemy asyncio session
    :return: dict
    """

    user = await UserCRUD.get_user(session=session, user_id=permission_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    permissions = ScopesManager.get_role_permission(role=user.role)

    log_handler.log_security_event(
        "Permission check",
        severity="low",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": permission_request.user_id,
            "target_username": permission_request.username,
            "check_resource": permission_request.resource,
            "role_name": permission_request.action,
            "action": "check_permission",
            "resource": "admin_routes",
        },
    )

    return permissions


@admin_router.get("/user-role/{user_id}")
async def get_user_role(
    user_id: UUID,
    current_user: Annotated[TokenData, Security(get_current_user, scopes=["ad:gr"])],
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scopes operation: Get a user's roles.

    :param user_id: The UUID of the user whose roles to return
    :param current_user: the User accessing the route
    :param session: SQLAlchemy asyncio session
    :return: dict
    """

    user = await UserCRUD.get_user(session=session, user_id=user_id)
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
    return {"user_id": user.id, "username": user.username, "role": user.role.value}
