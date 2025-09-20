import os
import sys
from typing import Dict, List

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure Casbin uses the testing DB
TEST_DB_PATH = "./test_auth.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["DATABASE_URL"] = TEST_DB_URL


@pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=True)
async def test_app():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    import app.main as main_module
    from app.casbin.casbin_config import startup_casbin
    from app.utils import database as db

    test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    db.engine = test_engine
    db.AsyncSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    db.metadata = SQLModel.metadata

    async with db.engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)

    application = main_module.app

    await startup_casbin(application, TEST_DB_URL)

    try:
        yield application
    finally:
        await db.engine.dispose()


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=True)
async def default_user(test_app):
    from app.casbin.casbin_helpers import casbin_subject
    from app.users.user_crud import UserCRUD
    from app.users.user_models import User
    from app.users.user_schemas import UserCreate
    from app.utils import database as db

    user_dict: Dict[str, User] = {}
    test_user_list: dict = {
        "test_admin": "admin",
        "test_moderator": "moderator",
        "test_authenticated": "authenticated",
        "test_user": "tester",
    }
    async with db.AsyncSessionLocal() as session:
        for test_user, role in test_user_list.items():
            user_in = UserCreate(
                username=f"{test_user}_user",
                email=f"{test_user}@example.com",
                password="UkeV3BNUIL7x/n0J",
            )
            user: User = await UserCRUD.create_user(session, user_in)
            if role in ["admin", "moderator"]:
                await test_app.state.casbin_enforcer.add_role_for_user(
                    user=casbin_subject(user.id), role=role
                )
            user_dict[role] = user
        yield user_dict


@pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=True)
async def default_pages(default_user):
    from app.pages.page_models import Page
    from app.utils import database as db

    pages_list: List[Page] = []
    pages_list.append(
        Page(
            title=f"{default_user['admin'].username}'s page",
            body=f"{default_user['admin'].username} they have the role admin",
            user_id=default_user["admin"].id,
        )
    )
    pages_list.append(
        Page(
            title=f"{default_user['moderator'].username}'s page",
            body=f"{default_user['moderator'].username} they have the role moderator",
            user_id=default_user["moderator"].id,
        )
    )
    async with db.AsyncSessionLocal() as session:
        session.add_all(pages_list)
        await session.commit()

    yield pages_list
