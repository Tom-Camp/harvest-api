from casbin import AsyncEnforcer
from sqlalchemy.ext.asyncio import AsyncSession

from app.casbin.casbin_config import create_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.casbin.default_policies import policies
from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_schemas import UserCreate
from app.utils.config import settings
from app.utils.database import AsyncSessionLocal

logger = get_logger(__name__)


async def setup_initial_admin(session: AsyncSession, enforcer: AsyncEnforcer) -> str:
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
        log_handler.log_security_event(
            event="Initial user created",
            severity="low",
            context={
                "username": admin_user.username,
                "user_id": admin_user.id,
            },
        )

        await enforcer.add_role_for_user(casbin_subject(admin_user.id), "admin")
        log_handler.log_security_event(
            event="User deleted",
            severity="moderate",
            context={
                "actor_id": "default",
                "actor_username": "default",
                "target_user_id": admin_user.id,
                "target_username": admin_user.username,
                "action": "add_admin_role",
            },
        )

        return admin_user.username
    else:
        logger.info("Admin user already exists")
        return existing_admin.username


async def setup_casbin_policies(enforcer: AsyncEnforcer) -> None:
    await enforcer.add_policies(rules=policies)


async def initialize_data() -> None:
    logger.info("Casbin setup")
    async with AsyncSessionLocal() as session:
        async_enforcer = await create_casbin_enforcer(
            db_url=settings.casbin_database_url
        )
        await setup_casbin_policies(enforcer=async_enforcer)
        await setup_initial_admin(session=session, enforcer=async_enforcer)
