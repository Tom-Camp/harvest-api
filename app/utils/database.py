from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.utils.config import settings

DATABASE_URL = settings.postgres_uri

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,  # set True for SQL echo during development
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    # If using migrations (Alembic), prefer running migrations instead of create_all
    # and remove the call above. [tutorial sources suggest create_all for demos]


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
