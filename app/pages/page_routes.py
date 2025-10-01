from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_object, casbin_subject, is_owner
from app.logging import get_logger, log_handler
from app.pages.page_crud import PageCRUD
from app.pages.page_models import Page
from app.pages.page_schemas import PageCreate, PageList, PageRead, PageUpdate
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

page_router = APIRouter(prefix="/pages")


@page_router.post("/", response_model=Page)
async def create_page(
    page: PageCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Page:
    """
    A route to create a new page

    :param session: The SQLAlchemy asyncio AsyncSession
    :param page: The PageCreate object; pages.page_schemas.PageCreate
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: Page
    """

    subject: str = casbin_subject(current_user.id)
    allowed = enforcer.enforce(subject, "page", "create")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    new_page = await PageCRUD.create_page(session, page, current_user.id)
    log_handler.log_business_event(
        event="Page create",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "page_id": new_page.id,
            "page_title": new_page.title,
            "action": "create_page",
            "resource": "page_routes",
        },
    )

    return new_page


@page_router.get("/", response_model=list[PageList])
async def read_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> list[PageList]:
    """
    A route to get all pages

    :param skip: The number of pages to skip
    :param limit: The number of pages to return
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: list of PageList objects
    """

    pages = await PageCRUD.get_pages(session, skip=skip, limit=limit)
    return [PageList.model_validate(page) for page in pages]


@page_router.get("/my", response_model=list[PageList])
async def read_my_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PageList]:
    """
    A route to get all pages

    :param skip: The number of pages to skip
    :param limit: The number of pages to return
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :return: list of PageList objects
    """

    pages = await PageCRUD.get_user_pages(
        session, current_user.id, skip=skip, limit=limit
    )
    return [PageList.model_validate(page) for page in pages]


@page_router.get("/{page_id}", response_model=PageRead)
async def read_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> PageRead:
    """
    A route to get a single page

    :param page_id: The UUID of the page
    :param session: The SQLAlchemy asyncio AsyncSession
    :return: PageRead object; pages.page_schemas.PageRead
    """

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@page_router.put("/{page_id}", response_model=Page)
async def update_page(
    page_id: UUID,
    page_update: PageUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Page | None:
    """
    A route to update a single page

    :param page_id: The UUID of the page
    :param page_update: The PageUpdate object; pages.page_schemas.PageUpdate
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: Page or None
    """

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    user_subject = casbin_subject(current_user.id)
    page_resource = casbin_object("pa", page.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, page_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, page):
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_page = await PageCRUD.update_page(session, page_id, page_update)
    if updated_page:
        log_handler.log_business_event(
            event="Page updated",
            context={
                "actor_id": current_user.id,
                "event_type": "security",
                "actor_username": current_user.username,
                "page_id": updated_page.id,
                "page_title": updated_page.title,
                "action": "update_page",
                "resource": "page_routes",
            },
        )
    return updated_page


@page_router.delete("/{page_id}")
async def delete_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a single page

    :param page_id: The UUID of the page
    :param session: The SQLAlchemy asyncio AsyncSession
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    user_subject = casbin_subject(current_user.id)
    page_resource = casbin_object("pa", page.id)

    # Check RBAC permissions
    allowed = enforcer.enforce(user_subject, page_resource, "update")

    # If RBAC fails, check ownership manually
    if not allowed and not is_owner(user_subject, page):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not await PageCRUD.delete_page(session, page_id):
        raise HTTPException(status_code=404, detail="Page not found")

    log_handler.log_business_event(
        event="Page deleted",
        context={
            "actor_id": current_user.id,
            "actor_username": current_user.username,
            "page_id": page.id,
            "page_title": page.title,
            "action": "delete_page",
            "resource": "page_routes",
        },
    )

    return {"message": "Page deleted successfully"}
