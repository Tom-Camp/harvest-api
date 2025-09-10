import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.casbin.casbin_config import AsyncCasbinManager
from app.users.role_crud import RoleCRUD
from app.users.user_schemas import RoleCreate, UserCreate
from app.users.users_crud import UserCRUD
from app.utils.config import settings
from app.utils.database import create_db_and_tables, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_initial_roles(session: AsyncSession):
    roles_data = [
        {"name": "admin", "description": "System administrator with full access"},
        {"name": "moderator", "description": "Moderator with limited admin access"},
        {"name": "user", "description": "Regular user with basic access"},
    ]

    created_roles = []
    for role_data in roles_data:
        existing_role = await RoleCRUD.get_role_by_name(session, role_data["name"])
        if not existing_role:
            role = RoleCreate(**role_data)
            created_role = await RoleCRUD.create_role(session, role)
            created_roles.append(created_role)
            logger.info(f"Created role: {created_role.name}")
        else:
            logger.info(f"Role already exists: {role_data['name']}")
            created_roles.append(existing_role)

    return created_roles


async def setup_initial_admin(
    session: AsyncSession,
    casbin_manager: AsyncCasbinManager,
) -> str:
    admin_data = {
        "username": settings.INITIAL_USER_NAME,
        "email": settings.INITIAL_USER_MAIL,
        "password": settings.INITIAL_USER_PASS,
        "is_active": True,
    }

    existing_admin = await UserCRUD.get_user_by_username(
        session=session, username=admin_data.get("username")  # type: ignore
    )
    if not existing_admin:
        admin_create = UserCreate(**admin_data)
        admin_user = await UserCRUD.create_user(session, admin_create)
        print(admin_user)
        logger.info(f"Created admin user: {admin_user.username}")

        admin_role = await RoleCRUD.get_role_by_name(session, "admin")
        if admin_role:
            await RoleCRUD.assign_role_to_user(session, admin_user.id, admin_role.id)
            logger.info("Assigned admin role to admin user in database")

        user_identifier = f"user:{admin_user.username}"
        await casbin_manager.add_role_for_user(user_identifier, "admin")
        logger.info("Assigned admin role to admin user in Casbin")

        return admin_user.username
    else:
        logger.info("Admin user already exists")
        return existing_admin.username


async def setup_casbin_policies(casbin_manager: AsyncCasbinManager) -> None:
    # Clear any existing policies before seeding
    await casbin_manager.clear_policy()

    # Optional: seed grouping/role relationships here if needed
    # Prefer assigning real users to roles, which setup_initial_admin already does
    # via casbin_manager.add_role_for_user("user:<username>", "admin")
    user_roles: List[tuple] = [
        ("user:admin", "moderator"),
    ]
    for user, role in user_roles:
        await casbin_manager.add_grouping_policy(user, role)

    # Seed RBAC policies (p rules)
    policies = [
        ("admin", "*", "*"),
        ("moderator", "user", "read"),
        ("moderator", "user", "write"),
        ("moderator", "page", "*"),
        ("moderator", "role", "read"),
        ("user", "page", "read"),
        ("user", "page", "create"),
    ]
    for p in policies:
        await casbin_manager.add_policy(*p)


async def initialize_data(casbin_manager: AsyncCasbinManager) -> None:
    logger.info("Starting initial data setup...")
    # 1) Create application tables
    await create_db_and_tables()

    # 2) Casbin tables + enforcer are already initialized in lifespan via casbin_manager.init()
    #    so do NOT call init_casbin_tables() here anymore.

    # 3) Seed policies
    await setup_casbin_policies(casbin_manager=casbin_manager)

    # 4) Seed roles and admin user
    session_maker = get_session()
    async with session_maker() as session:
        await setup_initial_roles(session)
        admin = await setup_initial_admin(
            session=session, casbin_manager=casbin_manager
        )
        logger.info(f"Admin user created: username={admin}")
        await session.commit()

    logger.info("Initial data setup completed!")
