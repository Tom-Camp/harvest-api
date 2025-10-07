from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import Depends, HTTPException

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.garden_models import Garden
from app.models.user_models import User
from app.schemas.bed_schemas import BedCreate
from app.schemas.garden_schemas import GardenCreate
from app.services.bed_service import BedService
from app.services.garden_service import GardenService

logger = get_logger(__name__)


def get_bed_service() -> BedService:
    return BedService(session=AsyncSessionLocal())


def get_garden_service() -> GardenService:
    return GardenService(session=AsyncSessionLocal())


async def add_default_bed(garden_id: UUID, service: BedService = Depends(BedService)):
    """
    Add a default bed to the default garden for a new User.

    :param service: BedService; services.bed_service.BedService
    :param garden_id: The garden UUID
    """

    bed = BedCreate(
        name="Default bed",
        description="A garden bed",
        garden_id=garden_id,
    )
    await service.create_bed(bed=bed)


async def add_default_garden(
    user: User, service: GardenService = Depends(get_garden_service)
):
    """
    Add a default garden for a new User.

    :param user: The new User object
    :param service: GardenService; services.garden_service.GardenService
    """

    garden = GardenCreate(
        name="Default garden",
        description="Garden added when user created",
        location="Lebanon, Kansas",
        is_private=False,
    )
    default_garden = await service.create_garden(garden=garden, user=user)
    if default_garden:
        await add_default_bed(garden_id=default_garden.id)
        session = AsyncSessionLocal()
        await session.refresh(default_garden, ["beds"])

        log_handler.log_security_event(
            "add_default_garden",
            severity="moderate",
            context={
                "event_type": "registration",
                "user_name": user.username,
                "user_id": user.id,
                "garden_id": default_garden.id,
                "resource": "auth_routes",
            },
        )
    else:
        log_handler.log_security_event(
            "default_garden_create_failed",
            severity="moderate",
            context={
                "event_type": "registration",
                "user_name": user.username,
                "user_id": user.id,
                "action": "default_garden_failed",
                "resource": "auth_routes",
            },
        )
    return default_garden


async def garden_check_access(
    garden_id: UUID,
    enforcer: AsyncEnforcer,
    current_user: User,
    action: str,
):
    """
    Access control function for Garden routes

    :param garden_id: Unique ID for the Garden
    :param enforcer: Casbin enforcer
    :param current_user: The user accessing the route
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    session = AsyncSessionLocal()
    garden = await session.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    user_subject = casbin_subject(current_user.id)
    garden_resource = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, action)

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return garden


async def garden_note_check_access(
    garden_id: UUID,
    enforcer: AsyncEnforcer,
    current_user: User,
    action: str,
):
    """
    Access control function for Garden routes

    :param garden_id: Unique ID for the Garden
    :param enforcer: Casbin enforcer
    :param current_user: The user accessing the route
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    session = AsyncSessionLocal()
    garden = await session.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, action)

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")
