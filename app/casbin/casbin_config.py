from pathlib import Path
from typing import List, Optional

from casbin import AsyncEnforcer
from casbin_async_sqlalchemy_adapter import Adapter as AsyncAdapter
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.utils.config import settings


class AsyncCasbinManager:

    _instance: Optional["AsyncCasbinManager"] = None

    def __new__(cls) -> "AsyncCasbinManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_engine"):
            return

        self._engine: AsyncEngine = create_async_engine(
            settings.postgres_uri, echo=False, future=True
        )

        self._adapter: Optional[AsyncAdapter] = None

        self._enforcer: Optional[AsyncEnforcer] = None

        self._ready: bool = False

    async def init(self) -> None:
        if self._ready:
            return

        self._adapter = AsyncAdapter(self._engine)
        await self._adapter.create_table()

        model_path = Path(__file__).with_name("casbin_model.conf")
        if not model_path.is_file():
            raise FileNotFoundError(f"Casbin model not found: {model_path}")

        self._enforcer = AsyncEnforcer(
            model_path.as_posix(), self._adapter, enable_log=True
        )

        await self._enforcer.load_policy()
        self._ready = True

    async def close(self) -> None:
        await self._engine.dispose()
        self._ready = False

    async def _ensure_ready(self) -> None:
        if not self._ready:
            await self.init()

    async def enforce(self, sub: str, obj: str, act: str) -> bool:
        await self._ensure_ready()
        assert self._enforcer is not None
        return self._enforcer.enforce(sub, obj, act)

    async def add_role_for_user(self, user: str, role: str) -> bool:
        await self._ensure_ready()
        assert self._enforcer is not None
        added = await self._enforcer.add_role_for_user(user, role)
        await self._enforcer.save_policy()
        return added

    async def delete_role_for_user(self, user: str, role: str) -> bool:
        await self._ensure_ready()
        assert self._enforcer is not None
        removed = await self._enforcer.delete_role_for_user(user, role)
        await self._enforcer.save_policy()
        return removed

    async def get_roles_for_user(self, user: str) -> List[str]:
        await self._ensure_ready()
        assert self._enforcer is not None
        return await self._enforcer.get_roles_for_user(user)

    async def get_users_for_role(self, role: str) -> List[str]:
        await self._ensure_ready()
        assert self._enforcer is not None
        return await self._enforcer.get_users_for_role(role)

    async def add_policy(self, *rule: str) -> bool:
        await self._ensure_ready()
        assert self._enforcer is not None
        added = await self._enforcer.add_policy(*rule)
        await self._enforcer.save_policy()
        return added

    async def remove_policy(self, *rule: str) -> bool:
        await self._ensure_ready()
        assert self._enforcer is not None
        removed = await self._enforcer.remove_policy(*rule)
        await self._enforcer.save_policy()
        return removed

    async def get_enforcer(self) -> AsyncEnforcer:
        await self._ensure_ready()
        assert self._enforcer is not None
        return self._enforcer

    async def clear_policy(self) -> None:
        await self._ensure_ready()
        assert self._enforcer is not None
        self._enforcer.clear_policy()
        await self._enforcer.save_policy()

    async def add_grouping_policy(self, *rule: str) -> None:
        await self._ensure_ready()
        assert self._enforcer is not None
        await self._enforcer.add_grouping_policy(*rule)
        await self._enforcer.save_policy()
