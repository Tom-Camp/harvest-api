from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.gardens.garden_crud import GardenCRUD
from app.users.user_models import User


async def garden_check_access(
    garden_id: UUID,
    session: AsyncSession,
    enforcer: AsyncEnforcer,
    current_user: User,
    action: str,
):
    """
    Access control function for Garden routes

    :param garden_id: Unique ID for the Garden
    :param session: SQLAlchemy asyncio AsyncSession
    :param enforcer: Casbin enforcer
    :param current_user: The user accessing the route
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    garden = await GardenCRUD.get_garden(session=session, garden_id=garden_id)
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
