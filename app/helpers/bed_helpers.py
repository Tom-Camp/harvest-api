from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.beds.bed_crud import BedCRUD
from app.beds.bed_schemas import BedRead
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.gardens.garden_models import Garden
from app.users.user_models import User


async def bed_check_access(
    garden_id: UUID,
    current_user: User,
    session: AsyncSession,
    enforcer: AsyncEnforcer,
    action: str,
):
    """
    Access control function for plant routes

    :param garden_id: The unique ID for the Garden that the Bed is associated with
    :param current_user: the User accessing the route; users.users_models.User
    :param session: SQLAlchemy asyncio AsyncSession
    :param enforcer: Casbin enforcer
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
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
    session: AsyncSession,
    enforcer: AsyncEnforcer,
    action: str,
) -> tuple[BedRead, Garden]:
    """
    Access control function for plant routes

    :param bed_id: The unique ID for the Bed that the BedNote is associated with
    :param current_user: the User accessing the route; users.users_models.User
    :param session: SQLAlchemy asyncio AsyncSession
    :param enforcer: Casbin enforcer
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    bed = await BedCRUD.get_bed(session=session, bed_id=bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Not found")

    garden = await GardenCRUD.get_garden(session, bed.garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Not found")

    user_subject: str = casbin_subject(current_user.id)
    garden_resource: str = casbin_object("ga", garden.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, garden_resource, action)

    if not allowed and not is_owner(user_subject, garden):
        raise HTTPException(status_code=403, detail="Forbidden")

    return bed, garden
