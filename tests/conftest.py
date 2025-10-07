import base64
import os

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel

from tests.test_db import TestingSessionLocal, engine

os.environ["TEST_DB"] = "sqlite+aiosqlite:///./test_app.db"

# Import after env is set so settings pick them up
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(loop_scope="session", scope="session")
def anyio_backend():
    # Use asyncio backend for async tests
    return "asyncio"


@pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=True)
async def app_lifespan():
    # Explicitly run FastAPI lifespan for the whole session
    async with LifespanManager(app):
        SQLModel.metadata.create_all(bind=engine)
        yield


@pytest_asyncio.fixture
async def client(app_lifespan):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
def basic_auth_alice_header() -> dict[str, str]:
    # Matches BasicAuth in app: user "alice"
    token = base64.b64encode(b"alice:password").decode("ascii")
    return {"Authorization": f"Basic {token}"}


@pytest_asyncio.fixture(loop_scope="class", scope="class", autouse=False)
async def default_user():
    from app.casbin.casbin_helpers import casbin_subject
    from app.models.user_models import User
    from app.schemas.user_schemas import UserCreate
    from app.services.user_service import UserService

    service = UserService(session=TestingSessionLocal())

    user_dict: dict[str, User] = dict()
    test_user_list: dict = {
        "test_admin": "admin",
        "test_moderator": "moderator",
        "test_authenticated": "authenticated",
        "test_user": "tester",
    }
    for test_user, role in test_user_list.items():
        user_in = UserCreate(
            username=f"{test_user}_user",
            email=f"{test_user}@example.com",
            password="UkeV3BNUIL7x/n0J",
        )
        user: User = await service.create_user(user=user_in)
        await app.state.casbin_enforcer.add_role_for_user(
            user=casbin_subject(user.id), role="authenticated"
        )
        if role in ["admin", "moderator"]:
            await app.state.casbin_enforcer.add_role_for_user(
                user=casbin_subject(user.id), role=role
            )
        user_dict[role] = user
    yield user_dict


#
# @pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=False)
# async def default_pages(default_user):
#     from app.pages.page_models import Page
#     from app.utils import database as db
#
#     pages_list: list[Page] = [
#         Page(
#             title=f"{default_user['admin'].username}'s page",
#             body=f"{default_user['admin'].username} they have the role admin",
#             user_id=default_user["admin"].id,
#         ),
#         Page(
#             title=f"{default_user['moderator'].username}'s page",
#             body=f"{default_user['moderator'].username} they have the role moderator",
#             user_id=default_user["moderator"].id,
#         ),
#     ]
#     async with db.AsyncSessionLocal() as session:
#         session.add_all(pages_list)
#         await session.commit()
#
#     yield pages_list
#
#
# @pytest_asyncio.fixture(scope="function", autouse=False)
# async def default_gardens(default_user):
#     from app.auth.auth_routes import add_default_garden
#     from app.gardens.garden_models import Garden
#     from app.utils import database as db
#
#     garden_dict: dict[str, Garden] = dict()
#     async with db.AsyncSessionLocal() as session:
#         for role, user in default_user.items():
#             garden_dict[role] = await add_default_garden(user=user, session=session)
#     yield garden_dict
