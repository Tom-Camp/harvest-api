from uuid import UUID

from app.core.auth.role_scopes import ROLE_SCOPES
from app.core.auth.scopes import SCOPES
from app.users.user_models import Role


class ScopesManager:

    @staticmethod
    def get_scopes_for_role(role: str) -> list[str]:
        """Get all scopes assigned to a role"""
        try:
            role_enum = Role(role)
            return ROLE_SCOPES[role_enum].copy()
        except (ValueError, KeyError):
            return []

    @staticmethod
    def has_scope(user_scopes: list[str], required_scope: str) -> bool:
        """Check if user has a specific scope"""
        return required_scope in user_scopes

    @staticmethod
    def has_all_scopes(user_scopes: list[str], required_scopes: list[str]) -> bool:
        """Check if user has all required scopes"""
        return all(scope in user_scopes for scope in required_scopes)

    @staticmethod
    def has_any_scope(user_scopes: list[str], required_scopes: list[str]) -> bool:
        """Check if user has at least one of the required scopes"""
        return any(scope in user_scopes for scope in required_scopes)

    @staticmethod
    def is_owner(
        user_scopes: list[str], required_scope: str, user_id: UUID, entity_owner: UUID
    ):
        return (
            True if required_scope in user_scopes and user_id == entity_owner else False
        )

    @staticmethod
    def get_role_permission(role: Role):
        return [SCOPES.get(scope, "") for scope in ROLE_SCOPES.get(role, "")]
