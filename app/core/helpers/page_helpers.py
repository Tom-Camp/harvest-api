from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import HTTPException

from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.models.page_models import Page
from app.models.user_models import User
from app.services.page_service import PageService


async def page_check_access(
    page_id: UUID,
    service: PageService,
    enforcer: AsyncEnforcer,
    current_user: User,
    action: str,
) -> Page:
    """
    Access control function for Garden routes

    :param page_id: Unique ID for the Page
    :param service: PageService; services.page_service.PageService
    :param enforcer: Casbin enforcer
    :param current_user: The user accessing the route
    :param action: The action for the enforcer to check; create, read, update, delete
    :return: Return the BedRead and Garden objects
    """

    page = await service.get_page(page_id=page_id)
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
