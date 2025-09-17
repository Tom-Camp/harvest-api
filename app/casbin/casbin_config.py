import os
from typing import List

from casbin import AsyncEnforcer
from casbin_async_sqlalchemy_adapter import Adapter as AsyncAdapter
from fastapi import Request

from app.casbin.casbin_helpers import casbin_subject, is_owner
from app.casbin.default_policies import DEFAULT_ADMIN_USERS, DEFAULT_POLICIES
from app.logging import get_logger, log_handler
from app.utils.exceptions import CasbinInitializationError

logger = get_logger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "casbin_model.conf")


async def create_casbin_enforcer(db_url: str) -> AsyncEnforcer:
    """Create Casbin enforcer with database adapter"""
    adapter = AsyncAdapter(db_url)
    enforcer = AsyncEnforcer(MODEL_PATH, adapter)
    enforcer.add_function("is_owner", is_owner)

    await adapter.create_table()
    await enforcer.load_policy()

    return enforcer


async def initialize_default_policies(enforcer: AsyncEnforcer):
    """Initialize default policies from single source"""
    logger.info("Initializing default policies...")

    for policy in DEFAULT_POLICIES:
        # Check if policy already exists
        exists = enforcer.has_policy(*policy)
        if not exists:
            success = await enforcer.add_policy(*policy)
            if success:
                logger.info(f"Added policy: {policy}")
            else:
                logger.warning(f"Failed to add policy: {policy}")
        else:
            logger.warning(f"Policy already exists: {policy}")

    await enforcer.save_policy()

    log_handler.log_security_event(
        "Default policies loaded",
        severity="high",
        context={
            "actor_id": "startup",
            "actor_username": "lifespan",
            "policies": DEFAULT_POLICIES,
            "action": "initialize_default_policies",
            "resource": "casbin_config",
        },
    )


async def setup_admin_users(
    enforcer: AsyncEnforcer, admin_user_ids: List | None = None
):
    """Setup admin users with admin role"""
    admin_ids = admin_user_ids or DEFAULT_ADMIN_USERS

    for admin_id in admin_ids:
        admin_subject = casbin_subject(admin_id)

        # Add admin role if not exists
        has_admin = await enforcer.has_role_for_user(admin_subject, "admin")
        if not has_admin:
            success = await enforcer.add_role_for_user(admin_subject, "admin")
            if success:
                log_handler.log_security_event(
                    "Role added on setup",
                    severity="high",
                    context={
                        "actor_id": "startup",
                        "actor_username": "lifespan",
                        "user_id": admin_id,
                        "role": "admin",
                        "action": "setup_admin_users",
                        "resource": "casbin_config",
                    },
                )
            else:
                log_handler.log_security_event(
                    "Role added on setup failed",
                    severity="high",
                    context={
                        "actor_id": "startup",
                        "actor_username": "lifespan",
                        "user_id": admin_id,
                        "role": "admin",
                        "action": "setup_admin_users",
                        "resource": "casbin_config",
                    },
                )
        else:
            log_handler.log_security_event(
                "User has role",
                severity="low",
                context={
                    "actor_id": "startup",
                    "actor_username": "lifespan",
                    "user_id": admin_id,
                    "role": "admin",
                    "action": "setup_admin_users",
                    "resource": "casbin_config",
                },
            )

    await enforcer.save_policy()


async def startup_casbin(app, db_url: str, admin_user_ids: List | None = None):
    """Complete Casbin initialization for FastAPI startup"""
    try:
        logger.info("=== Casbin Initialization ===")

        # Create enforcer
        enforcer = await create_casbin_enforcer(db_url)
        app.state.casbin_enforcer = enforcer

        # Initialize default policies
        await initialize_default_policies(enforcer)

        # Setup admin users
        await setup_admin_users(enforcer, admin_user_ids)

        # Validation
        total_policies = len(enforcer.get_policy())
        total_roles = len(enforcer.get_grouping_policy())

        log_handler.log_security_event(
            "Casbin initialized successfully",
            severity="low",
            context={
                "total_policies": total_policies,
                "total_roles_assigned": total_roles,
                "action": "startup_casbin",
                "resource": "casbin_config",
            },
        )
    except CasbinInitializationError as cie:
        logger.error(f"Casbin initialization failed: {cie}")
        raise


def get_casbin_enforcer(request: Request) -> AsyncEnforcer:
    """FastAPI dependency to get Casbin enforcer"""
    return request.app.state.casbin_enforcer
