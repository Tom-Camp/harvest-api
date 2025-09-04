import os

import casbin
from casbin_async_sqlalchemy_adapter import Adapter

from app.utils.database import DATABASE_URL


class AsyncCasbinManager:
    _instance = None
    _enforcer = None
    _adapter = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncCasbinManager, cls).__new__(cls)
        return cls._instance

    async def get_enforcer(self):
        if self._enforcer is None:
            self._adapter = Adapter(DATABASE_URL)

            model_path = os.path.join(os.path.dirname(__file__), "./casbin_model.conf")

            self._enforcer = casbin.Enforcer(model_path, self._adapter)

            await self._load_initial_policies()

        return self._enforcer

    async def _load_initial_policies(self):
        e = self._enforcer

        # Clear existing policies (optional)
        e.clear_policy()

        # Add some default roles and permissions
        # Format: role, page, action
        default_policies = [
            ("admin", "*", "*"),  # Admin can do anything
            ("user", "page", "read"),
            ("user", "page", "read"),
            ("user", "page", "create"),
            ("moderator", "page", "*"),
            ("moderator", "user", "read"),
            ("moderator", "user", "write"),
        ]

        # Add policies
        for policy in default_policies:
            e.add_policy(*policy)

        # Save policies to database
        e.save_policy()

    async def check_permission(self, user: str, resource: str, action: str) -> bool:
        """Check if user has permission to perform action on resource"""
        enforcer = await self.get_enforcer()
        return enforcer.enforce(user, resource, action)

    async def add_role_for_user(self, user: str, role: str) -> bool:
        """Add role to user"""
        enforcer = await self.get_enforcer()
        result = enforcer.add_role_for_user(user, role)
        enforcer.save_policy()
        return result

    async def remove_role_for_user(self, user: str, role: str) -> bool:
        """Remove role from user"""
        enforcer = await self.get_enforcer()
        result = await enforcer.remove_role_for_user(user, role)
        enforcer.save_policy()
        return result

    async def get_roles_for_user(self, user: str) -> list:
        """Get all roles for a user"""
        enforcer = await self.get_enforcer()
        return enforcer.get_roles_for_user(user)

    async def get_users_for_role(self, role: str) -> list:
        """Get all users with a specific role"""
        enforcer = await self.get_enforcer()
        return enforcer.get_users_for_role(role)

    async def add_policy(self, role: str, resource: str, action: str) -> bool:
        """Add a policy rule"""
        enforcer = await self.get_enforcer()
        result = enforcer.add_policy(role, resource, action)
        enforcer.save_policy()
        return result

    async def remove_policy(self, role: str, resource: str, action: str) -> bool:
        """Remove a policy rule"""
        enforcer = await self.get_enforcer()
        result = enforcer.remove_policy(role, resource, action)
        enforcer.save_policy()
        return result


# Global instance
casbin_manager = AsyncCasbinManager()
