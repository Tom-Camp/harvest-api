from app.models.users import Role, User
from app.utils.config import settings
from app.utils.security import hash_password


def initial_user() -> tuple[Role, User]:
    role = Role(
        name="admin",
        description="Superuser role",
    )
    hashed_password = hash_password(settings.INITIAL_USER_PASS)
    new_user = User(
        username=settings.INITIAL_USER_NAME,
        email=settings.INITIAL_USER_MAIL,
        hashed_password=hashed_password,
        role=role,
    )

    return role, new_user
