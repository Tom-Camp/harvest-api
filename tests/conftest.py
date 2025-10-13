from typing import Dict, List

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth.auth_routes import add_default_garden
from app.gardens.garden_models import Garden
from app.main import app
from app.pages.page_models import Page
from app.users.user_crud import UserCRUD
from app.users.user_models import Role, User
from app.users.user_schemas import UserCreate, UserUpdateRole
from app.utils.database import get_db
from tests.test_db import TestingSessionLocal, engine, metadata


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def default_user(db_session):

    user_dict: Dict[str, User] = dict()
    test_user_list: dict = {
        "test_admin": "administrator",
        "test_moderator": "moderator",
        "test_authenticated": "authenticated",
        "test_user": "authenticated",
    }
    for test_user, role in test_user_list.items():
        user_in = UserCreate(
            username=f"{test_user}",
            email=f"{test_user}@example.com",
            password="UkeV3BNUIL7xn0J",
        )
        user: User = await UserCRUD.create_user(db_session, user_in)
        new_user = await UserCRUD.update_user_role(
            session=db_session,
            user_id=user.id,
            role=UserUpdateRole(role=Role(role)),
        )
        user_dict[f"{test_user}"] = new_user
    yield user_dict


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def default_pages(default_user, db_session):

    pages_list: List[Page] = [
        Page(
            title=f"{default_user['admin'].username}'s page",
            body=f"{default_user['admin'].username} they have the role admin",
            user_id=default_user["admin"].id,
        ),
        Page(
            title=f"{default_user['moderator'].username}'s page",
            body=f"{default_user['moderator'].username} they have the role moderator",
            user_id=default_user["moderator"].id,
        ),
    ]

    db_session.add_all(pages_list)
    await db_session.commit()

    yield pages_list


@pytest_asyncio.fixture(loop_scope="function", scope="function", autouse=False)
async def default_gardens(default_user, db_session):
    garden_dict: dict[str, Garden] = dict()
    for role, user in default_user.items():
        garden_dict[role] = await add_default_garden(user=user, session=db_session)
    yield garden_dict
