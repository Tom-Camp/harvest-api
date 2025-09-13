from casbin import AsyncEnforcer
from casbin_async_sqlalchemy_adapter import Adapter as AsyncAdapter
from fastapi import Request

MODEL_PATH = "app/casbin/casbin_model.conf"


async def create_casbin_enforcer(db_url: str) -> AsyncEnforcer:
    adapter = AsyncAdapter(db_url)
    enforcer = AsyncEnforcer(MODEL_PATH, adapter)
    await adapter.create_table()
    await enforcer.load_policy()
    return enforcer


def get_casbin_enforcer(request: Request) -> AsyncEnforcer:
    return request.app.state.casbin_enforcer
