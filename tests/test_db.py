from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


metadata = SQLModel.metadata
