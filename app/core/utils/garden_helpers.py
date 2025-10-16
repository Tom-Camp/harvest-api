from uuid import UUID

from fastapi import HTTPException

from app.core.auth.scopes_manager import ScopesManager
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.user_models import User
from app.schemas.auth_schemas import TokenData
from app.schemas.bed_schemas import BedCreate
from app.schemas.garden_schemas import GardenCreate
from app.services.bed_service import BedService
from app.services.garden_service import GardenService

logger = get_logger(__name__)


def check_garden_access(current_user: TokenData, garden_user: UUID, scope: str):

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope=scope
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope=f"{scope}:own",
        user_id=current_user.id,
        entity_owner=garden_user,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")


async def add_default_garden(user: User):
    """
    Add a default garden for a new User.

    :param user: The new User object
    """
    async with AsyncSessionLocal() as session:
        garden_service = GardenService(session=session)
        bed_service = BedService(session=session)

    garden = GardenCreate(
        name="Default garden",
        description="Garden added when user created",
        location="Lebanon, Kansas",
        is_private=False,
    )
    default_garden = await garden_service.create_garden(garden=garden, user_id=user.id)
    if default_garden:
        bed = BedCreate(
            name="Default bed",
            description="A garden bed",
            garden_id=default_garden.id,
        )
        await bed_service.create_bed(bed=bed)
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
