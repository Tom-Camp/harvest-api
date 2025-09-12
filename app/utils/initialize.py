from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.casbin.casbin_config import casbin_manager
from app.casbin.casbin_helpers import casbin_subject
from app.logging import get_logger
from app.users.user_crud import UserCRUD
from app.users.user_schemas import UserCreate
from app.utils.config import settings
from app.utils.database import get_db

logger = get_logger(__name__)


async def setup_initial_admin(session: AsyncSession = Depends(get_db)) -> str:
    admin_data = {
        "username": settings.INITIAL_USER_NAME,
        "email": settings.INITIAL_USER_MAIL,
        "password": settings.INITIAL_USER_PASS,
        "is_active": True,
    }

    existing_admin = await UserCRUD.get_user_by_username(
        session=session, username=str(admin_data.get("username", ""))
    )
    if not existing_admin:
        admin_create = UserCreate(**admin_data)
        admin_user = await UserCRUD.create_user(session, admin_create)

        await casbin_manager.add_role_for_user(casbin_subject(admin_user.id), "admin")
        logger.info("Assigned admin role to admin user in Casbin")

        return admin_user.username
    else:
        logger.info("Admin user already exists")
        return existing_admin.username


async def setup_casbin_policies() -> None:
    policies = [
        ("admin", "*", "*"),
        ("moderator", "user", "read"),
        ("moderator", "user", "write"),
        ("moderator", "user", "delete"),
        ("user", "page", "read"),
        ("user", "page", "create"),
        ("user", "page", "delete"),
    ]
    for p in policies:
        await casbin_manager.add_policy(*p)


async def initialize_data() -> None:
    logger.info("Casbin setup")
    await setup_casbin_policies()
    await setup_initial_admin()
