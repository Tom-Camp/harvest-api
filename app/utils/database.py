from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.utils.config import settings


def get_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.postgres_uri
    return create_async_engine(url, echo=True)


def get_session(engine=None) -> async_sessionmaker:
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables(engine=None):
    if engine is None:
        engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def init_casbin_tables():
    from casbin_async_sqlalchemy_adapter import Adapter

    engine: AsyncEngine = get_engine()
    adapter = await Adapter(engine).create_table()
    return adapter
