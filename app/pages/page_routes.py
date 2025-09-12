from typing import List, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_active_user
from app.casbin.casbin_config import casbin_manager
from app.casbin.casbin_helpers import casbin_object, casbin_subject
from app.logging import get_logger, log_handler
from app.pages.page_crud import PageCRUD
from app.pages.page_models import Page
from app.pages.page_schemas import PageList, PageRead
from app.users.user_models import User
from app.utils.database import get_db

logger = get_logger(__name__)

page_router = APIRouter(prefix="/pages")


@page_router.post("/", response_model=Page)
async def create_page(
    page: Page,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Page:
    subject: str = casbin_subject(current_user.id)
    allowed = await casbin_manager.enforce(sub=subject, obj="/pages", act="write")
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    new_page = await PageCRUD.create_page(session, page, current_user.id)
    logger.info(
        "Page create",
        actor_id=current_user.id,
        actor_username=current_user.username,
        page_id=new_page.id,
        page_title=new_page.title,
        action="content_creation",
    )
    object_id: str = casbin_object(identifier="p", object_id=new_page.id)
    await casbin_manager.add_policy(
        sub=subject,
        obj=object_id,
        act="update",
    )
    log_handler.log_security_event(
        "Permission policy update",
        actor_id=current_user.id,
        actor_username=current_user.username,
        page_id=new_page.id,
        page_title=new_page.title,
        action="page_update",
    )

    await casbin_manager.add_policy(
        sub=subject,
        obj=object_id,
        act="delete",
    )
    log_handler.log_security_event(
        "Permission policy delete",
        actor_id=current_user.id,
        actor_username=current_user.username,
        page_id=new_page.id,
        page_title=new_page.title,
        action="page_delete",
    )

    return new_page


@page_router.get("/", response_model=List[PageList])
async def read_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):
    return await PageCRUD.get_pages(session, skip=skip, limit=limit)


@page_router.get("/my", response_model=List[PageList])
async def read_my_pages(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Sequence:
    return await PageCRUD.get_user_pages(
        session, current_user.id, skip=skip, limit=limit
    )


@page_router.get("/{page_id}", response_model=PageRead)
async def read_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@page_router.put("/{page_id}", response_model=Page)
async def update_page(
    page_id: UUID,
    page_update: Page,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Page | None:
    allowed = await casbin_manager.enforce(
        casbin_subject(current_user.id), casbin_object("p", page_id), "update"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    updated_page = await PageCRUD.update_page(session, page_id, page_update)
    if updated_page:
        log_handler.log_security_event(
            "Page updated",
            actor_id=current_user.id,
            actor_username=current_user.username,
            page_id=updated_page.id,
            page_title=updated_page.title,
            action="page_update",
        )
    return updated_page


@page_router.delete("/{page_id}")
async def delete_page(
    page_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    allowed = await casbin_manager.enforce(
        casbin_subject(current_user.id), casbin_object("p", page_id), "delete"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    page = await PageCRUD.get_page(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if not PageCRUD.delete_page(session, page_id):
        raise HTTPException(status_code=404, detail="Page not found")

    log_handler.log_security_event(
        "Page deleted",
        actor_id=current_user.id,
        actor_username=current_user.username,
        page_id=page.id,
        page_title=page.title,
        action="page_delete",
    )

    return {"message": "Page deleted successfully"}
