from starlette.authentication import BaseUser
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN
from starlette.types import ASGIApp, Receive, Scope, Send

from app.logging import get_logger

logger = get_logger(__name__)


class CasbinMiddleware:
    def __init__(self, app: ASGIApp, enforcer) -> None:
        self.app = app
        self._enforcer = enforcer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        enforcer = self._enforcer() if callable(self._enforcer) else self._enforcer

        if (
            await self._enforce(scope, receive, enforcer)
            or scope["method"] == "OPTIONS"
        ):
            await self.app(scope, receive, send)
            return
        else:
            response = JSONResponse(status_code=HTTP_403_FORBIDDEN, content="Forbidden")
            await response(scope, receive, send)
            return

    @staticmethod
    async def _enforce(scope: Scope, receive: Receive, enforcer) -> bool:
        request = Request(scope, receive)
        path = request.url.path
        method = request.method
        if "user" not in scope:
            raise RuntimeError(
                "Casbin Middleware must work with an Authentication Middleware"
            )

        assert isinstance(request.user, BaseUser)
        user = (
            request.user.display_name if request.user.is_authenticated else "anonymous"
        )

        return enforcer.enforce(user, path, method)
