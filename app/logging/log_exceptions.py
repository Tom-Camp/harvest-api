import structlog
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging.log_handler import log_handler


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id", "unknown"
    )

    if exc.status_code >= 500:
        log_handler.log_error(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )
    elif exc.status_code >= 400:
        log_handler.log_security_event(
            "Client error occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
            severity="low" if exc.status_code < 403 else "medium",
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "correlation_id": correlation_id,
            "error_type": "http_exception",
        },
    )


async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id", "unknown"
    )

    log_handler.log_security_event(
        "Request validation failed",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
        severity="low",
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "correlation_id": correlation_id,
            "error_type": "validation_error",
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = structlog.contextvars.get_contextvars().get(
        "correlation_id", "unknown"
    )

    log_handler.log_error(
        "Unhandled exception occurred",
        exception=exc,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id,
            "error_type": "internal_error",
        },
    )


def setup_exception_handlers(app):
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
