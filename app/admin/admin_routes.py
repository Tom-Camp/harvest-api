from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.permission_schemas import PermissionCheck, RoleRequest
from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin")


@admin_router.post("/assign-role")
async def assign_role(
    role_request: RoleRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    user = await UserCRUD.get_user(session=session, user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = enforcer.enforce(casbin_subject(current_user.id), "role", "add")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    await enforcer.add_role_for_user(
        user=casbin_subject(role_request.user_id), role=role_request.role_name
    )
    log_handler.log_security_event(
        "Role assigned to user",
        severity="medium",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": role_request.user_id,
            "target_username": role_request.username,
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
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    user = await UserCRUD.get_user(session=session, user_id=role_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = enforcer.enforce(casbin_subject(current_user.id), "role", "delete")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    await enforcer.delete_role_for_user(
        user=casbin_subject(role_request.user_id), role=role_request.role_name
    )

    log_handler.log_security_event(
        "Role removed from user",
        severity="medium",
        context={
            "event_type": "security",
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": role_request.user_id,
            "target_username": role_request.username,
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
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    user = await UserCRUD.get_user(session=session, user_id=permission_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = enforcer.enforce(casbin_subject(current_user.id), "policy", "read")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    has_permission = enforcer.enforce(
        casbin_subject(permission_request.user_id),
        permission_request.resource,
        permission_request.action,
    )

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

    return {
        "user": permission_request.username,
        "resource": permission_request.resource,
        "action": permission_request.action,
        "has_permission": has_permission,
    }


@admin_router.get("/user-roles/{user_id}")
async def get_user_roles(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    user = await UserCRUD.get_user(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not foond")

    allowed = enforcer.enforce(casbin_subject(current_user.id), "role", "read")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    roles = await enforcer.get_roles_for_user(casbin_subject(user_id))

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
    return {"user_id": user_id, "roles": roles}


@admin_router.get("/role-users/{role_name}")
async def get_role_users(
    role_name: str,
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:

    allowed = enforcer.enforce(casbin_subject(current_user.id), "role", "read")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    users = await enforcer.get_users_for_role(role_name)

    log_handler.log_security_event(
        "List user with role",
        severity="low",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_role": role_name,
            "action": "get_role_users",
            "resource": "admin_routes",
        },
    )
    return {"role": role_name, "users": [user.replace("user:", "") for user in users]}
