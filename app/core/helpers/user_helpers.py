from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.models.user_models import User
from app.services.user_service import UserService


async def admin_check_access(
    service: UserService,
    user_id: UUID,
    current_user: User,
    enforcer: AsyncEnforcer,
    subject: str,
    action: str,
):
    """
    Access control for admin routes.

    :param service: UserService; services.user_service.UserService
    :param user_id: The user ID for the user to whom we are adding a role
    :param current_user: The user adding the role
    :param enforcer: Casbin AsyncEnforcer
    :param subject: The Casbin subject to check
    :param action: The Casbin action to check
    """

    user = await service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = enforcer.enforce(casbin_subject(current_user.id), subject, action)
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


async def user_check_access(
    service: UserService,
    user_id: UUID,
    current_user: User,
    enforcer: AsyncEnforcer,
    action: str,
) -> User:
    """
    Access control for user routes.

    :param service: UserService; services.user_service.UserService
    :param user_id: The user ID for the user to whom we are adding a role
    :param current_user: The user adding the role
    :param enforcer: Casbin AsyncEnforcer
    :param action: The Casbin action to check
    """

    existing_user = await service.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_subject = casbin_subject(current_user.id)
    user_resource = casbin_object("us", user_id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, user_resource, action)

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, existing_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    return existing_user
