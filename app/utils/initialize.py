from app.models.users import Role, User
from app.utils.auth import pwd_context
from app.utils.config import settings


def initial_user() -> tuple[Role, User]:
    role = Role(
        name="admin",
        description="Superuser role",
    )
    hashed_password = pwd_context.hash(settings.initial_user_pass)
    new_user = User(
        username=settings.initial_user_name,
        email=settings.initial_user_mail,
        hashed_password=hashed_password,
        role=role,
    )

    return role, new_user
