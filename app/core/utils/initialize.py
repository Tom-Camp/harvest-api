from uuid import UUID

from app.core.utils.config import settings
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.schemas.user_schemas import UserCreate
from app.services.user_service import UserService

logger = get_logger(__name__)


def get_user_service() -> UserService:
    return UserService(session=AsyncSessionLocal())


async def setup_initial_admin() -> UUID:
    """
    Sets up the initial admin user

    :param session: The SQLAlchemy asyncio AsyncSession
    :return: UUID
    """

    admin_data = {
        "username": settings.INITIAL_USER_NAME,
        "email": settings.INITIAL_USER_MAIL,
        "password": settings.INITIAL_USER_PASS,
        "location": settings.INITIAL_USER_LOCATION,
    }

    service = get_user_service()
    existing_admin = await service.get_user_by_username(
        username=admin_data.get("username", "")
    )
    if not existing_admin:
        admin_create = UserCreate(**admin_data)
        admin_user = await service.create_user(user=admin_create)
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
