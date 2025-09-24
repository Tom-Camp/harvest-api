from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import get_logger, log_handler
from app.users.user_crud import UserCRUD
from app.users.user_schemas import UserCreate
from app.utils.config import settings

logger = get_logger(__name__)


async def setup_initial_admin(session: AsyncSession) -> UUID:
    admin_data = {
        "username": settings.INITIAL_USER_NAME,
        "email": settings.INITIAL_USER_MAIL,
        "password": settings.INITIAL_USER_PASS,
        "location": settings.INITIAL_USER_LOCATION,
    }

    existing_admin = await UserCRUD.get_user_by_username(
        session=session, username=admin_data.get("username", "")
    )
    if not existing_admin:
        admin_create = UserCreate(**admin_data)
        admin_user = await UserCRUD.create_user(session, admin_create)
        log_handler.log_security_event(
            "Initial user created",
            severity="low",
            context={
                "actor_id": "startup",
                "actor_username": "lifespan",
                "username": admin_user.username,
                "user_id": admin_user.id,
                "action": "setup_initial_admin",
                "resource": "initialize",
            },
        )

        return admin_user.id
    else:
        logger.info("Admin user already exists")
        return existing_admin.id
