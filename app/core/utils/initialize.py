from app.core.utils.config import settings
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.user_models import Role
from app.schemas.user_schemas import UserCreate
from app.services.user_service import UserService

logger = get_logger(__name__)


def get_init_service() -> UserService:
    return UserService(session=AsyncSessionLocal)


async def setup_initial_admin():
    """Sets up the initial admin user"""

    admin_data = UserCreate(
        username=settings.INITIAL_USER_NAME,
        email=settings.INITIAL_USER_MAIL,
        password=settings.INITIAL_USER_PASS,
        location=settings.INITIAL_USER_LOCATION,
        role=Role.ADMIN,
    )

    service = get_init_service()
    existing_admin = await service.get_user_by_username(username=admin_data.username)
    if not existing_admin:
        admin_user = await service.create_user(user=admin_data)
        log_handler.log_security_event(
            "Admin user created",
            severity="high",
            context={
                "actor_id": "startup",
                "actor_username": "lifespan",
                "username": admin_user.username,
                "user_id": admin_user.id,
                "action": "setup_initial_admin",
                "resource": "initialize",
            },
        )
    else:
        logger.info("Admin user already exists")
