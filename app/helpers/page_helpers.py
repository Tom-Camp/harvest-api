from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.pages.page_crud import PageCRUD
from app.pages.page_models import Page
from app.users.user_models import User


async def page_check_access(
    page_id: UUID,
    session: AsyncSession,
    enforcer: AsyncEnforcer,
    current_user: User,
    action: str,
) -> Page:
    """
    Access control function for Garden routes

    :param page_id: Unique ID for the Page
    :param session: SQLAlchemy asyncio AsyncSession
    :param enforcer: Casbin enforcer
    :param current_user: The user accessing the route
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    user_subject = casbin_subject(current_user.id)
    page_resource = casbin_object("pa", page.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, page_resource, action)

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, page):
        raise HTTPException(status_code=403, detail="Forbidden")

    return page
