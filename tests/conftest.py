# tests/conftest.py
import asyncio
import os

import httpx
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from testcontainers.postgres import PostgresContainer


# ----------------------------------------------------------------------
# 1️⃣ Spin up a PostgreSQL container for the whole test session
# ----------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _postgres_container():
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    # Store the container on the pytest config object so we can read it later.
    pytest.config = getattr(pytest, "config", None)  # noqa: B009
    if pytest.config is not None:
        pytest.config._store["_postgres_container"] = container  # type: ignore[attr-defined]
    yield container
    container.stop()


# ----------------------------------------------------------------------
# 2️⃣ Inject env‑vars **before** any app code is imported
# ----------------------------------------------------------------------
def pytest_configure(config):
    container = getattr(config, "_store", {}).get("_postgres_container")  # type: ignore[attr-defined]
    if container is None:
        raise RuntimeError("Postgres test container not available")

    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)

    os.environ["POSTGRES_HOST"] = host
    os.environ["POSTGRES_PORT"] = str(port)
    os.environ["POSTGRES_USER"] = container.username
    os.environ["POSTGRES_PASSWORD"] = container.password
    os.environ["POSTGRES_DB"] = container.dbname

    # The Settings class reads these variables on import.
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("HASH_ALGORITHM", "HS256")


# ----------------------------------------------------------------------
# 3️⃣ Provide an asyncio event loop for pytest‑asyncio
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ----------------------------------------------------------------------
# 4️⃣ Import the FastAPI app **after** env‑vars are set
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def app():
    import app.main as main_mod

    return main_mod.app


# ----------------------------------------------------------------------
# 5️⃣ HTTP client wrapped in LifespanManager (starts the app)
# ----------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as async_client:
            yield async_client
