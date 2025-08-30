from fastapi_users.password import PasswordHelper

from app.models.users import Role, User
from app.utils.config import settings


def initial_user() -> tuple[Role, User]:
    role = Role(
        name="admin",
        description="Superuser role",
    )
    password_helper = PasswordHelper()
    new_user = User(
        username=settings.initial_user_name,
        email=settings.initial_user_mail,
        hashed_password=password_helper.hash(settings.initial_user_pass),
        role=role,
    )

    return role, new_user
