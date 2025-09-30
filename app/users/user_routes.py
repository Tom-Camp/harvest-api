from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_models import User
from app.users.user_schemas import UserRead, UserUpdate
from app.utils.database import get_db

logger = get_logger(__name__)

user_router = APIRouter(prefix="/users")


@user_router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> UserRead | None:
    """
    A route to return a User object for the current user

    :param current_user: The current user
    :param session: The SQLAlchemy asyncio AsyncSession
    :param enforcer: The Casbin AsyncEnforcer
    :return: User or None
    """

    user = await UserCRUD.get_user(
        session=session,
        user_id=current_user.id,
    )
    if user:
        await enforcer.add_role_for_user(
            user=casbin_subject(user.id), role="authenticated"
        )
    return user


@user_router.get("/", response_model=list[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    """
    A route to return a list of User objects for the current user

    :param skip: The number of users to skip
    :param limit: The number of users to return
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: list[UserRead]; users/user_schemas.py
    """

    users = await UserCRUD.get_users(session, skip=skip, limit=limit)
    return [UserRead.model_validate(user) for user in users]


@user_router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> UserRead:
    """
    A route to return a User object for the current user

    :param user_id: The UUID of the user
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: UserRead or None
    """

    allowed = enforcer.enforce(
        casbin_subject(current_user.id), casbin_object("us", user_id), "read"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = await UserCRUD.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("%s read user" % current_user.username)
    return user


@user_router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> UserRead:
    """
    A route to update a User object for the current user

    :param user_id: The UUID of the user
    :param user_update: The UserUpdate object; users/user_schemas.py
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: UserRead or None
    """

    existing_user = await UserCRUD.get_user(session, user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_subject = casbin_subject(current_user.id)
    user_resource = casbin_object("us", user_id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, user_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, existing_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    user = await UserCRUD.update_user(session, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a User object

    :param user_id: The UUID of the user
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    existing_user = await UserCRUD.get_user(session, user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_subject = casbin_subject(current_user.id)
    user_resource = casbin_object("us", user_id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, user_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, existing_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Delete Pages associated with the User

    if not await UserCRUD.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    await enforcer.delete_user(casbin_subject(user_id))

    log_handler.log_security_event(
        event="User deleted",
        severity="moderate",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "target_user_id": existing_user.id,
            "target_username": existing_user.username,
            "action": "delete_user",
            "resource": "user_routes",
        },
    )

    return {"message": f"User {existing_user.username} deleted successfully"}
