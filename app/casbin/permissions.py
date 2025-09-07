from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.models.users import User
from app.utils.auth import get_current_active_user
from app.utils.dependencies import get_casbin_manager


class AsyncPermissionChecker:
    def __init__(self, page: str, action: str):
        self.page = page
        self.action = action

    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        casbin_manager=Depends(get_casbin_manager),
    ):
        """Check if current user has permission"""
        user_identifier = f"user:{current_user.username}"

        has_permission = await casbin_manager.check_permission(
            user_identifier, self.page, self.action
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {self.action} on {self.page}",
            )

        return current_user


def require_permission(page: str, action: str):
    """Decorator to require specific permission"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(AsyncPermissionChecker(page, action)),
            **kwargs,
        ):
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_active_user),
            casbin_manager=Depends(get_casbin_manager),
            **kwargs,
        ):
            user_identifier = f"user:{current_user.username}"
            user_roles = await casbin_manager.get_roles_for_user(user_identifier)

            if role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required",
                )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


# Common permission dependencies
RequireAdmin = AsyncPermissionChecker("*", "*")
RequireUserRead = AsyncPermissionChecker("user", "read")
RequireUserWrite = AsyncPermissionChecker("user", "write")
RequirePageRead = AsyncPermissionChecker("page", "read")
RequirePageWrite = AsyncPermissionChecker("page", "write")


async def check_page_ownership(
    page_owner_id: str,
    current_user: User,
    casbin_manager=Depends(get_casbin_manager),
) -> bool:
    """Check if user owns the page or has admin privileges"""
    user_identifier = f"user:{current_user.username}"

    # Check if user is admin
    if await casbin_manager.check_permission(user_identifier, "*", "*"):
        return True

    # Check if user owns the page
    return str(page_owner_id) == str(current_user.id)


def require_ownership_or_permission(page: str, action: str):
    """Decorator to require page ownership OR specific permission"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_active_user),
            casbin_manager=Depends(get_casbin_manager),
            **kwargs,
        ):
            user_identifier = f"user:{current_user.username}"

            # Check if user has the general permission
            if await casbin_manager.check_permission(user_identifier, page, action):
                return await func(*args, current_user=current_user, **kwargs)

            # If no general permission, the specific ownership check should be done in the route
            # This decorator just ensures the user is authenticated
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
