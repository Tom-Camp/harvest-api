from uuid import UUID

from fastapi import Depends, HTTPException

from app.auth.auth import get_current_user
from app.casbin.casbin_config import casbin_manager
from app.users.user_models import User


def casbin_subject(user_id: UUID) -> str:
    return f"u:{user_id}"


def casbin_object(identifier: str, object_id: UUID) -> str:
    return f"{identifier}:{object_id}"


async def require_role(
    required_role: str, user: User = Depends(get_current_user)
) -> bool | HTTPException:
    roles = await casbin_manager.get_roles_for_user(casbin_subject(user.sub))
    if required_role not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Requires role '{required_role}'.",
        )
    return True
