import os
import sys

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure Casbin uses the testing DB
TEST_DB_PATH = "./test_auth.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["CASBIN_DB_URL"] = TEST_DB_URL


@pytest_asyncio.fixture
async def app():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    from sqlmodel import SQLModel

    import app.main as main_module
    from app.casbin.casbin_config import create_casbin_enforcer
    from app.utils import database as db
    from app.utils.config import settings

    test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    db.engine = test_engine
    db.AsyncSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    db.metadata = SQLModel.metadata

    async with db.engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)

    # Get the FastAPI app instance
    application = main_module.app

    # Initialize Casbin enforcer against testing DB (normally done in lifespan)
    enforcer = await create_casbin_enforcer(settings.casbin_database_url)
    application.state.casbin_enforcer = enforcer

    try:
        yield application
    finally:
        await db.engine.dispose()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
