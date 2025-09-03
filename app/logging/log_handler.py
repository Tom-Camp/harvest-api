from typing import Any, Optional

import structlog
from fastapi import Request


class StructlogHandler:

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def log_request_start(self, request: Request, **kwargs: Any) -> None:
        self.logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else {},
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length"),
            **kwargs,
        )

    def log_request_end(
        self, request: Request, response_status: int, duration: float, **kwargs: Any
    ) -> None:
        log_method = self._get_log_method_for_status(response_status)

        log_method(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response_status,
            duration_ms=round(duration * 1000, 2),
            **kwargs,
        )

    def log_business_event(self, event: str, **context: Any) -> None:
        self.logger.info(event, event_type="business", **context)

    def log_security_event(
        self, event: str, severity: str = "medium", **context: Any
    ) -> None:
        log_method = (
            self.logger.warning if severity in ["medium", "high"] else self.logger.info
        )

        log_method(event, event_type="security", severity=severity, **context)

    def log_performance_event(
        self, event: str, duration_ms: float, **context: Any
    ) -> None:
        log_level = self._get_performance_log_level(duration_ms)
        log_method = getattr(self.logger, log_level)

        log_method(event, event_type="performance", duration_ms=duration_ms, **context)

    def log_database_operation(
        self,
        operation: str,
        table: str | None = None,
        duration_ms: float | None = None,
        **context: Any,
    ) -> None:
        log_data: dict = {"event_type": "database", "operation": operation, **context}

        if table:
            log_data["table"] = table
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        self.logger.info(f"Database {operation}", **log_data)

    def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        method: str,
        status_code: int | None = None,
        duration_ms: float | None = None,
        **context: Any,
    ) -> None:
        log_data = {
            "event_type": "external_api",
            "service": service,
            "endpoint": endpoint,
            "method": method,
            **context,
        }

        if status_code is not None:
            log_data["status_code"] = status_code
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        log_method = (
            self._get_log_method_for_status(status_code)
            if status_code
            else self.logger.info
        )
        log_method(f"External API call to {service}", **log_data)

    def log_error(
        self, message: str, exception: Exception | None = None, **context: Any
    ) -> None:
        log_data = {"event_type": "error", **context}

        if exception:
            log_data.update(
                {
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception),
                }
            )

        self.logger.error(message, exc_info=exception is not None, **log_data)

    def _get_log_method_for_status(self, status_code: Optional[int]):
        if not status_code:
            return self.logger.info

        if status_code < 400:
            return self.logger.info
        elif status_code < 500:
            return self.logger.warning
        else:
            return self.logger.error

    @staticmethod
    def _get_performance_log_level(duration_ms: float) -> str:
        if duration_ms > 5000:  # 5 seconds
            return "error"
        elif duration_ms > 2000:  # 2 seconds
            return "warning"
        elif duration_ms > 1000:  # 1 second
            return "info"
        else:
            return "debug"


log_handler = StructlogHandler()
