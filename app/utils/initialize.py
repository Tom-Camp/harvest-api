from app.models.users import Role, User
from app.utils.config import settings
from app.utils.security import hash_password


def initial_user() -> tuple[Role, User]:
    role = Role(
        name="admin",
        description="Superuser role",
    )
    hashed_password = hash_password(settings.initial_user_pass)
    new_user = User(
        username=settings.initial_user_name,
        email=settings.initial_user_mail,
        hashed_password=hashed_password,
        role=role,
    )

    return role, new_user
