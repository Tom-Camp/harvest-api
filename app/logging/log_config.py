import logging.config
from typing import Any, List

import structlog

from app.utils.config import settings


def get_log_level() -> str:
    return settings.LOG_LEVEL


def is_development() -> bool:
    return settings.ENVIRONMENT == "development"


def get_structlog_processors(development: bool | None = None) -> List[Any]:
    if development is None:
        development = is_development()

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]

    if development:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.extend(
            [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
        )

    return processors


def configure_stdlib_logging() -> None:
    development = is_development()
    log_level = get_log_level()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": (
                        structlog.dev.ConsoleRenderer()
                        if development
                        else structlog.processors.JSONRenderer()
                    ),
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.TimeStamper(fmt="ISO"),
                        structlog.processors.add_log_level,
                    ],
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "plain",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": True,
                },
                "httpcore": {"level": "WARNING"},
                "httpx": {"level": "WARNING"},
                "uvicorn.access": {"level": "WARNING"},
            },
        }
    )


def configure_structlog() -> None:
    configure_stdlib_logging()

    structlog.configure(
        processors=get_structlog_processors(),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
