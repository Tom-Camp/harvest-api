from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.permission_schemas import PermissionCheck, RoleRequest
from app.auth.auth import get_current_active_user
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import Role, User
from app.users.user_schemas import UserUpdate
from app.utils.database import get_db

logger = get_logger(__name__)

admin_router = APIRouter(prefix="/admin")


@admin_router.post("/assign-role")
async def assign_role(
    role_request: RoleRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Casbin operation: Assign a role to user.

    :param role_request: Role to assign
    :param current_user: The user currently accessing the route
    :param session: SQLAlchemy asyncio session
    """

    user = await UserCRUD.update_user(
        session=session,
        user_id=role_request.user_id,
        user_update=UserUpdate(role=Role(role_request.role_name)),
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
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Casbin operation: Remove a role from a user.

    :param role_request: Role to remove
    :param current_user: The user currently accessing the route
    :param session: SQLAlchemy asyncio session
    """

    user = await UserCRUD.update_user(
        session=session,
        user_id=role_request.user_id,
        user_update=UserUpdate(role=Role.AUTHENTICATED),
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
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Casbin operation: Check user permissions.

    :param permission_request: PermissionCheck object containing the User ID, permission, and action
    :param current_user: Current user User object
    :param session: SQLAlchemy asyncio session
    :return: dict
    """

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
        "has_permission": True,
    }


#
# @admin_router.get("/user-roles/{user_id}")
# async def get_user_roles(
#     user_id: UUID,
#     current_user: User = Depends(get_current_active_user),
#     session: AsyncSession = Depends(get_db),
# ) -> dict:
#     """
#     Casbin operation: Get a user's roles.
#
#     :param user_id: The UUID of the user whose roles to return
#     :param current_user: Current user User object
#     :param session: SQLAlchemy asyncio session
#     :param enforcer: Casbin AsyncEnforcer object
#     :return: dict
#     """
#
#     log_handler.log_security_event(
#         "List user roles",
#         severity="low",
#         context={
#             "event_type": "security",
#             "actor_id": current_user.id,
#             "actor_username": current_user.username,
#             "target_user_id": user_id,
#             "action": "get_user_roles",
#             "resource": "admin_routes",
#         },
#     )
#     return {"user_id": user_id, "roles": user}
#
#
# @admin_router.get("/role-users/{role_name}")
# async def get_role_users(
#     role_name: str,
#     current_user: User = Depends(get_current_active_user),
#     enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
# ) -> dict:
#     """
#     Casbin operation: Return a list of users with the given role.
#
#     :param role_name: PermissionCheck object containing the User ID, permission, and action
#     :param current_user: Current user User object
#     :param enforcer: Casbin AsyncEnforcer object
#     :return: dict
#     """
#
#     allowed = enforcer.enforce(casbin_subject(current_user.id), "role", "read")
#     if not allowed:
#         raise HTTPException(status_code=403, detail="Forbidden")
#
#     users = await enforcer.get_users_for_role(role_name)
#
#     log_handler.log_security_event(
#         "List user with role",
#         severity="low",
#         context={
#             "actor_id": current_user.id,
#             "actor_username": current_user.username,
#             "target_role": role_name,
#             "action": "get_role_users",
#             "resource": "admin_routes",
#         },
#     )
#     return {"role": role_name, "users": [user.replace("user:", "") for user in users]}
