from uuid import UUID

from casbin import AsyncEnforcer
from fastapi import APIRouter, Depends, HTTPException

from app.casbin.casbin_config import get_casbin_enforcer
from app.casbin.casbin_helpers import casbin_subject
from app.core.auth import get_current_active_user
from app.core.helpers.page_helpers import page_check_access
from app.core.utils.database import AsyncSessionLocal
from app.logging import get_logger, log_handler
from app.models.page_models import Page
from app.models.user_models import User
from app.schemas.page_schemas import PageCreate, PageList, PageRead, PageUpdate
from app.services.page_service import PageService

logger = get_logger(__name__)

page_router = APIRouter(prefix="/pages")


def get_page_service() -> PageService:
    return PageService(session=AsyncSessionLocal())


@page_router.post("/", response_model=Page)
async def create_page(
    page: PageCreate,
    service: PageService = Depends(get_page_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Page:
    """
    A route to create a new page

    :param page: The PageCreate object; pages.page_schemas.PageCreate
    :param service: PageService; services.page_service.PageService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: Page
    """

    subject: str = casbin_subject(current_user.id)
    allowed = enforcer.enforce(subject, "page", "create")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    new_page = await service.create_page(page=page, user_id=current_user.id)
    log_handler.log_business_event(
        event="Create Page",
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
    service: PageService = Depends(get_page_service),
) -> list[PageList]:
    """
    A route to get all pages

    :param skip: The number of pages to skip
    :param limit: The number of pages to return
    :param service: PageService; services.page_service.PageService
    :return: list of PageList objects
    """

    pages = await service.get_pages(skip=skip, limit=limit)
    return [PageList.model_validate(page) for page in pages]


@page_router.get("/my", response_model=list[PageList])
async def read_my_pages(
    skip: int = 0,
    limit: int = 100,
    service: PageService = Depends(get_page_service),
    current_user: User = Depends(get_current_active_user),
) -> list[PageList]:
    """
    A route to get all pages

    :param skip: The number of pages to skip
    :param limit: The number of pages to return
    :param service: PageService; services.page_service.PageService
    :param current_user: The current user
    :return: list of PageList objects
    """

    pages = await service.get_user_pages(current_user.id, skip=skip, limit=limit)
    return [PageList.model_validate(page) for page in pages]


@page_router.get("/{page_id}", response_model=PageRead)
async def read_page(
    page_id: UUID,
    service: PageService = Depends(get_page_service),
) -> Page:
    """
    A route to get a single page

    :param page_id: The UUID of the page
    :param service: PageService; services.page_service.PageService
    :return: PageRead object; pages.page_schemas.PageRead
    """

    page = await service.get_page(page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@page_router.put("/{page_id}", response_model=Page)
async def update_page(
    page_id: UUID,
    page_update: PageUpdate,
    service: PageService = Depends(get_page_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> Page | None:
    """
    A route to update a single page

    :param page_id: The UUID of the page
    :param page_update: The PageUpdate object; pages.page_schemas.PageUpdate
    :param service: PageService; services.page_service.PageService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: Page or None
    """

    _ = await page_check_access(
        page_id=page_id,
        service=service,
        enforcer=enforcer,
        current_user=current_user,
        action="update",
    )

    updated_page = await service.update_page(page_id=page_id, page_update=page_update)
    if updated_page:
        log_handler.log_business_event(
            event="Update Page",
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
    service: PageService = Depends(get_page_service),
    current_user: User = Depends(get_current_active_user),
    enforcer: AsyncEnforcer = Depends(get_casbin_enforcer),
) -> dict:
    """
    A route to delete a single page

    :param page_id: The UUID of the page
    :param service: PageService; services.page_service.PageService
    :param current_user: The current user
    :param enforcer: The Casbin AsyncEnforcer
    :return: dict
    """

    page = await page_check_access(
        page_id=page_id,
        service=service,
        enforcer=enforcer,
        current_user=current_user,
        action="delete",
    )

    if not await service.delete_page(page_id=page_id):
        raise HTTPException(status_code=404, detail="Page not found")

    log_handler.log_business_event(
        event="Delete Page",
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
