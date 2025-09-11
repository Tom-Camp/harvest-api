from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.permission_schemas import AssignRoleRequest, PermissionCheck
from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import AsyncCasbinManager
from app.casbin.permissions import RequireAdmin
from app.logging import get_logger, log_handler
from app.users.role_crud import RoleCRUD
from app.users.user_models import User
from app.users.users_crud import UserCRUD
from app.utils.database import get_db
from app.utils.dependencies import get_casbin_manager

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin")


@admin_router.post("/assign-role")
async def assign_role(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireAdmin),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    user = await UserCRUD.get_user(session, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = await RoleCRUD.get_role_by_name(session, request.role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    await RoleCRUD.assign_role_to_user(session, request.user_id, role.id)

    user_identifier = f"user:{user.username}"
    await casbin_manager.add_role_for_user(user_identifier, request.role_name)
    log_handler.log_security_event(
        "Role %s assigned to user %s" % request.role_name,
        user.username,
        username=current_user.username,
    )

    return {"message": f"Role '{request.role_name}' assigned to user '{user.username}'"}


@admin_router.post("/remove-role")
async def remove_role(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireAdmin),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    user = await UserCRUD.get_user(session, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = await RoleCRUD.get_role_by_name(session, request.role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    await RoleCRUD.remove_role_from_user(session, request.user_id, role.id)

    user_identifier = f"user:{user.username}"
    await manager.delete_role_for_user(user_identifier, request.role_name)
    log_handler.log_security_event(
        "Role %s removed from user %s" % request.role_name,
        user.username,
        username=current_user.username,
    )

    return {
        "message": f"Role '{request.role_name}' removed from user '{user.username}'"
    }


@admin_router.post("/check-permission")
async def check_permission(
    request: PermissionCheck,
    current_user: User = Depends(get_current_active_user),
    manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    user_identifier: str = f"user:{current_user.username}"
    has_permission = await manager.enforce(
        sub=user_identifier,
        obj=request.resource,
        act=request.action,
    )
    return {
        "user": current_user.username,
        "resource": request.resource,
        "action": request.action,
        "has_permission": has_permission,
        "roles": manager.get_roles_for_user(user_identifier),
    }


@admin_router.get("/user-roles/{username}")
async def get_user_roles(
    username: str,
    current_user: User = Depends(RequireAdmin),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    user_identifier = f"user:{username}"
    roles = casbin_manager.get_roles_for_user(user_identifier)
    logger.info("%s listed %s role" % current_user.username, username)
    return {"username": username, "roles": roles}


@admin_router.get("/role-users/{role_name}")
async def get_role_users(
    role_name: str,
    current_user: User = Depends(RequireAdmin),
    casbin_manager: AsyncCasbinManager = Depends(get_casbin_manager),
):
    users = await casbin_manager.get_users_for_role(role_name)
    logger.info("%s listed the users with role" % current_user.username, role_name)
    return {"role": role_name, "users": [user.replace("user:", "") for user in users]}
