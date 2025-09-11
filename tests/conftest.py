# conftest.py
import asyncio
import os
import sys

import httpx
import pytest
import pytest_asyncio
import sqlalchemy.ext.asyncio as sa_async
from asgi_lifespan import LifespanManager
from testcontainers.postgres import PostgresContainer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app.logging import get_logger  # noqa: E402
from app.utils.config import settings  # noqa: E402
from app.utils.database import get_engine  # noqa: E402

pytest_plugins = ["pytest_asyncio"]

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def postgres():
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session", autouse=True)
def test_settings_env(postgres):
    host = postgres.get_container_host_ip()
    port = postgres.get_exposed_port(5432)
    os.environ["POSTGRES_HOST"] = host
    os.environ["POSTGRES_PORT"] = str(port)
    os.environ["POSTGRES_USER"] = postgres.username
    os.environ["POSTGRES_PASS"] = postgres.password
    os.environ["POSTGRES_DB"] = postgres.dbname

    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("HASH_ALGORITHM", "HS256")
    yield


@pytest_asyncio.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app(test_settings_env):
    import importlib

    import app.main as main_module

    importlib.reload(main_module)

    logger.debug("DATABASE: %s" % settings.postgres_uri)
    yield main_module.app


@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as async_client:
            yield async_client


@pytest.fixture(scope="function")
async def db_session():
    engine = get_engine()
    async with sa_async.AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            yield session
