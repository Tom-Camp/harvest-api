from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.core.utils.database import AsyncSessionLocal
from app.models.bed_models import Bed
from app.models.garden_models import Garden
from app.models.user_models import User
from app.schemas.bed_schemas import BedRead


async def bed_check_access(
    garden_id: UUID,
    current_user: User,
    enforcer: AsyncEnforcer,
    action: str,
):
    """
    Access control function for plant routes

    :param garden_id: The unique ID for the Garden that the Bed is associated with
    :param current_user: the User accessing the route; users.users_models.User
    :param enforcer: Casbin enforcer
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


async def bed_note_check_access(
    bed_id: UUID,
    current_user: User,
    enforcer: AsyncEnforcer,
    action: str,
) -> tuple[BedRead, Garden]:
    """
    Access control function for plant routes

    :param bed_id: The unique ID for the Bed that the BedNote is associated with
    :param current_user: the User accessing the route; users.users_models.User
    :param enforcer: Casbin enforcer
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    session = AsyncSessionLocal()

    bed = await session.get(Bed, bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await session.get(Garden, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, action)

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return bed, garden
