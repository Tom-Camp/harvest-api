import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.casbin.casbin_config import casbin_manager
from app.casbin.permissions import RequireAdmin
from app.crud.role_crud import RoleCRUD
from app.crud.users_crud import UserCRUD
from app.models.users import User
from app.schemas.permission_schemas import AssignRoleRequest, PermissionCheck
from app.utils.auth import get_current_active_user
from app.utils.database import get_session

admin_router = APIRouter(prefix="/admin")


@admin_router.post("/assign-role")
async def assign_role(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireAdmin),
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
    logging.info(
        "Role %s assigned to user %s by %s" % request.role_name,
        user.username,
        current_user.username,
    )

    return {"message": f"Role '{request.role_name}' assigned to user '{user.username}'"}


@admin_router.post("/remove-role")
async def remove_role(
    request: AssignRoleRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(RequireAdmin),
):
    user = await UserCRUD.get_user(session, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = await RoleCRUD.get_role_by_name(session, request.role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    await RoleCRUD.remove_role_from_user(session, request.user_id, role.id)

    user_identifier = f"user:{user.username}"
    await casbin_manager.remove_role_for_user(user_identifier, request.role_name)
    logging.info(
        "Role %s removed from user %s by %s" % request.role_name,
        user.username,
        current_user.username,
    )

    return {
        "message": f"Role '{request.role_name}' removed from user '{user.username}'"
    }


@admin_router.post("/check-permission")
async def check_permission(
    request: PermissionCheck, current_user: User = Depends(get_current_active_user)
):
    user_identifier = f"user:{current_user.username}"
    has_permission = casbin_manager.check_permission(
        user_identifier, request.resource, request.action
    )

    return {
        "user": current_user.username,
        "resource": request.resource,
        "action": request.action,
        "has_permission": has_permission,
        "roles": casbin_manager.get_roles_for_user(user_identifier),
    }


@admin_router.get("/user-roles/{username}")
async def get_user_roles(username: str, current_user: User = Depends(RequireAdmin)):
    user_identifier = f"user:{username}"
    roles = casbin_manager.get_roles_for_user(user_identifier)
    logging.info("%s listed %s role" % current_user.username, username)
    return {"username": username, "roles": roles}


@admin_router.get("/role-users/{role_name}")
async def get_role_users(role_name: str, current_user: User = Depends(RequireAdmin)):
    users = await casbin_manager.get_users_for_role(role_name)
    logging.info("%s listed the users with role" % current_user.username, role_name)
    return {"role": role_name, "users": [user.replace("user:", "") for user in users]}
