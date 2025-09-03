import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import structlog

from app.logging.log_handler import log_handler


def log_function_call(
    operation_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    log_duration: bool = True,
    event_type: str = "function_call",
):

    def decorator(func: Callable) -> Callable:
        func_name = (
            operation_name
            or f"{getattr(func, '__module__', 'unknown')}.{func.__qualname__}"
        )
        logger = structlog.get_logger(getattr(func, "__module__", "unknown"))

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _execute_with_logging(
                    func,
                    func_name,
                    logger,
                    event_type,
                    log_args,
                    log_result,
                    log_duration,
                    args,
                    kwargs,
                )

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(
                    _execute_with_logging(
                        func,
                        func_name,
                        logger,
                        event_type,
                        log_args,
                        log_result,
                        log_duration,
                        args,
                        kwargs,
                    )
                )

            return sync_wrapper

    return decorator


async def _execute_with_logging(
    func: Callable,
    func_name: str,
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    log_args: bool,
    log_result: bool,
    log_duration: bool,
    args: tuple,
    kwargs: dict,
) -> Any:
    log_data: Dict[str, Any] = {
        "event_type": event_type,
        "function": func_name,
    }

    if log_args:
        log_data.update(
            {
                "args": _sanitize_args(args),
                "kwargs": _sanitize_kwargs(kwargs),
            }
        )

    start_time = time.time()
    logger.info(f"Starting {func_name}", **log_data)

    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        duration_ms = (time.time() - start_time) * 1000

        success_data = {"status": "success"}
        if log_duration:
            success_data["duration_ms"] = str(round(duration_ms, 2))
        if log_result:
            success_data["result"] = _sanitize_result(result)

        logger.info(f"Completed {func_name}", **{**log_data, **success_data})

        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        error_data = {
            "status": "error",
            "exception_type": type(e).__name__,
            "exception_message": str(e),
        }
        if log_duration:
            error_data["duration_ms"] = str(round(duration_ms, 2))

        logger.error(f"Failed {func_name}", exc_info=True, **{**log_data, **error_data})

        raise


def log_database_operation(table: str | None = None, operation: str | None = None):

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            log_handler.log_database_operation(
                operation=f"{op_name}_start",
                table=table,
            )

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000
                log_handler.log_database_operation(
                    operation=f"{op_name}_success",
                    table=table,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_handler.log_error(
                    f"Database operation {op_name} failed",
                    exception=e,
                    table=table,
                    duration_ms=duration_ms,
                )
                raise

        return wrapper

    return decorator


def log_external_api_call(service: str, endpoint: str | None = None):

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                status_code = getattr(result, "status_code", None)

                log_handler.log_external_api_call(
                    service=service,
                    endpoint=endpoint or func.__name__,
                    method="unknown",  # Could be enhanced to extract from kwargs
                    status_code=status_code,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_handler.log_error(
                    f"External API call to {service} failed",
                    exception=e,
                    service=service,
                    endpoint=endpoint,
                    duration_ms=duration_ms,
                )
                raise

        return wrapper

    return decorator


def _sanitize_args(args: tuple) -> List[Any]:
    return [_sanitize_value(arg) for arg in args[:5]]  # Limit to first 5 args


def _sanitize_kwargs(kwargs: dict) -> Dict[str, Any]:
    sensitive_keys = {"password", "token", "secret", "key", "auth"}

    sanitized: Dict[str, Any] = {}
    for key, value in list(kwargs.items())[:10]:  # Limit to first 10 kwargs
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = _sanitize_value(value)

    return sanitized


def _sanitize_result(result: Any) -> Any:
    return _sanitize_value(result)


def _sanitize_value(
    value: Any,
) -> Union[str, int, float, bool, None, List[Any], Dict[str, Any]]:
    if isinstance(value, (str, int, float, bool, type(None))):
        if isinstance(value, str) and len(value) > 200:
            return f"{value[:200]}..."
        return value
    elif isinstance(value, (list, tuple)):
        if len(value) > 5:
            return f"<{type(value).__name__} with {len(value)} items>"
        return [_sanitize_value(v) for v in value]
    elif isinstance(value, dict):
        if len(value) > 5:
            return f"<dict with {len(value)} keys>"
        return {k: _sanitize_value(v) for k, v in list(value.items())[:5]}
    else:
        return f"<{type(value).__name__} object>"
