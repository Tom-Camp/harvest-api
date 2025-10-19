from sqlmodel import select

from app.core.auth.auth_helpers import get_password_hash
from app.core.utils.config import settings
from app.core.utils.database import get_db
from app.logging import get_logger, log_handler
from app.models.role_models import Role
from app.models.user_models import User

logger = get_logger(__name__)


async def create_roles() -> list[Role]:
    roles: list = [
        Role(
            name="administrator",
            description="Administrator with full access",
        ),
        Role(
            name="moderator",
            description="Can edit some content",
        ),
        Role(
            name="authenticated",
            description="Can create gardens",
        ),
    ]
    async for session in get_db():
        session.add_all(roles),
        await session.commit()
    return roles


async def setup_initial_admin():
    """Sets up the initial admin user"""
    roles = await create_roles()
    admin_roles = [role for role in roles if role.name != "moderator"]
    hashed_password = get_password_hash(settings.INITIAL_USER_PASS)
    admin_username = settings.INITIAL_USER_NAME
    admin_user = User(
        username=admin_username,
        email=settings.INITIAL_USER_MAIL,
        hashed_password=hashed_password,
        roles=admin_roles,
    )

    async for session in get_db():
        statement = select(User).where(User.username == admin_username)
        result = await session.execute(statement)
        existing_admin = result.scalars().first()
        if not existing_admin:
            session.add(admin_user)
            await session.commit()
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
