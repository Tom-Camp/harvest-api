from casbin import AsyncEnforcer
from casbin_async_sqlalchemy_adapter import Adapter as AsyncAdapter

from app.utils.config import settings


class CasbinManager:

    def __init__(self):
        model_path = "app/casbin/casbin_model.conf"

        self.adapter = AsyncAdapter(settings.casbin_database_url)

        self.enforcer = AsyncEnforcer(model_path, self.adapter)

    async def enforce(self, sub: str, obj: str, act: str) -> bool:
        return self.enforcer.enforce(sub, obj, act)

    async def add_policy(self, sub: str, obj: str, act: str) -> None:
        await self.enforcer.add_policy(sub, obj, act)

    async def remove_policy(self, sub: str, obj: str, act: str) -> None:
        await self.enforcer.remove_policy(sub, obj, act)

    async def add_role_for_user(self, user: str, role: str) -> None:
        await self.enforcer.add_role_for_user(user, role)

    async def delete_role_for_user(self, user: str, role: str) -> None:
        await self.enforcer.delete_role_for_user(user, role)

    async def delete_roles_for_user(self, user: str) -> list[str]:
        return await self.enforcer.delete_roles_for_user(user)

    async def get_roles_for_user(self, user: str) -> list[str]:
        return await self.enforcer.get_roles_for_user(user)

    async def get_users_for_role(self, user: str) -> list[str]:
        return await self.enforcer.get_users_for_role(user)


casbin_manager = CasbinManager()
