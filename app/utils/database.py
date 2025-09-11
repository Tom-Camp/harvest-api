from typing import AsyncGenerator

from casbin_async_sqlalchemy_adapter import Adapter
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.logging import get_logger
from app.utils.config import settings

logger = get_logger(__name__)


def get_engine() -> AsyncEngine:
    return create_async_engine(settings.postgres_uri, echo=False, future=True)


def get_session(engine=None) -> async_sessionmaker:
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


SessionLocal = async_sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables(engine: AsyncEngine | None = None):
    if engine is None:
        engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def init_casbin_tables(engine: AsyncEngine | None = None):
    if engine is None:
        engine = get_engine()
    adapter = Adapter(engine)
    await adapter.create_table()
    return adapter
