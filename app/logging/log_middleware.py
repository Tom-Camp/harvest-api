import time
import uuid
from typing import Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging.log_handler import log_handler


class LoggingMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list[str]] = None,
        include_request_body: bool = False,
        include_response_body: bool = False,
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._should_skip_logging(request):
            return await call_next(request)

        correlation_id = self._get_or_create_correlation_id(request)
        start_time = time.time()

        self._setup_logging_context(request, correlation_id)

        await self._log_request_start(request)

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            log_handler.log_request_end(request, response.status_code, duration)

            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            log_handler.log_error(
                "Request failed with exception",
                exception=e,
                duration_ms=round(duration * 1000, 2),
            )

            raise  # Re-raise the exception

    def _should_skip_logging(self, request: Request) -> bool:
        return request.url.path in self.excluded_paths

    @staticmethod
    def _get_or_create_correlation_id(request: Request) -> str:
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        return correlation_id

    def _setup_logging_context(self, request: Request, correlation_id: str) -> None:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            client_ip=self._get_client_ip(request),
            method=request.method,
            path=request.url.path,
        )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _log_request_start(self, request: Request) -> None:
        extra_data = {}

        if self.include_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Note: This consumes the request body, so you might need to
                # implement body caching if you need it later
                body = await request.body()
                if body:
                    extra_data["request_body_size"] = len(body)
                    # Only log small bodies to avoid log bloat
                    if len(body) < 1000:
                        extra_data["request_body"] = body.decode(
                            "utf-8", errors="ignore"
                        )
            except (ValueError, RuntimeError):
                pass

        log_handler.log_request_start(request, **extra_data)


def create_logging_middleware(
    excluded_paths: Optional[list[str]] = None,
    include_request_body: bool = False,
    include_response_body: bool = False,
) -> type:

    class CustomLoggingMiddleware(LoggingMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(
                app,
                excluded_paths=excluded_paths,
                include_request_body=include_request_body,
                include_response_body=include_response_body,
            )

    return CustomLoggingMiddleware
