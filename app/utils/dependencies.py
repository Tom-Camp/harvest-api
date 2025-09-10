from fastapi import Request

from app.casbin.casbin_config import AsyncCasbinManager


def get_casbin_manager(request: Request) -> AsyncCasbinManager:
    return request.app.state.casbin_manager
