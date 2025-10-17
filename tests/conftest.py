import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.v1.admin_routes import get_admin_service
from app.api.v1.auth_routes import get_auth_service
from app.api.v1.page_routes import get_page_service
from app.api.v1.user_routes import get_user_service
from app.core.auth.auth import get_current_user_service
from app.main import app
from app.models.garden_models import Garden
from app.models.page_models import Page
from app.models.user_models import Role, User
from app.schemas.garden_schemas import GardenCreate
from app.schemas.user_schemas import UserCreate, UserUpdateRole
from app.services.garden_service import GardenService
from app.services.page_service import PageService
from app.services.user_service import UserService
from tests.test_db import TestingSessionLocal, engine, get_db, metadata


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
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_auth_service():
        yield UserService(session=db_session)

    def override_get_admin_service():
        yield UserService(session=db_session)

    def override_get_current_user_service():
        yield UserService(session=db_session)

    def override_get_page_service():
        yield PageService(session=db_session)

    def override_get_user_service():
        yield UserService(session=db_session)

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    app.dependency_overrides[get_admin_service] = override_get_admin_service
    app.dependency_overrides[get_current_user_service] = (
        override_get_current_user_service
    )
    app.dependency_overrides[get_page_service] = override_get_page_service
    app.dependency_overrides[get_user_service] = override_get_user_service
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    # Cleanup overrides after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def default_user(db_session):
    service = UserService(session=db_session)
    user_dict: dict[str, User] = dict()
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
        user: User = await service.create_user(user=user_in)
        new_user = await service.update_user_role(
            user_id=user.id,
            role=UserUpdateRole(role=Role(role)),
        )
        user_dict[f"{test_user}"] = new_user
    yield user_dict


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def default_pages(default_user, db_session):
    pages_list: list[Page] = [
        Page(
            title=f"{default_user['test_admin'].username}'s page",
            body=f"{default_user['test_admin'].username} they have the role admin",
            user_id=default_user["test_admin"].id,
        ),
        Page(
            title=f"{default_user['test_moderator'].username}'s page",
            body=f"{default_user['test_moderator'].username} they have the role moderator",
            user_id=default_user["test_moderator"].id,
        ),
    ]

    db_session.add_all(pages_list)
    await db_session.commit()

    yield pages_list


@pytest_asyncio.fixture(loop_scope="function", scope="function", autouse=False)
async def default_gardens(default_user, db_session):
    service = GardenService(session=db_session)
    garden_dict: dict[str, Garden] = dict()
    for role, user in default_user.items():
        garden_dict[user.username] = await service.create_garden(
            garden=GardenCreate(
                name="Default garden",
                description="Garden added when user created",
                location="Lebanon, Kansas",
                is_private=False,
            ),
            user_id=user.id,
        )
    yield garden_dict
