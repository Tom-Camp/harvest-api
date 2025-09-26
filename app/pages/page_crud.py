from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.logging import get_logger
from app.pages.page_models import Page
from app.pages.page_schemas import PageCreate, PageUpdate

logger = get_logger(__name__)


class PageCRUD:
    @staticmethod
    async def create_page(
        session: AsyncSession, page: PageCreate, user_id: UUID
    ) -> Page:
        db_page = Page(**page.model_dump(), user_id=user_id)
        session.add(db_page)
        await session.commit()
        await session.refresh(db_page)
        return db_page

    @staticmethod
    async def get_page(session: AsyncSession, page_id: UUID) -> Page | None:
        return await session.get(Page, page_id)

    @staticmethod
    async def get_pages(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Page]:
        statement = select(Page).offset(skip).limit(limit)
        result = await session.execute(statement)
        pages = result.scalars().all()
        return pages

    @staticmethod
    async def get_user_pages(
        session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Page]:
        statement = (
            select(Page)
            .where(Page.__table__.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        pages = result.scalars().all()
        return pages

    @staticmethod
    async def update_page(
        session: AsyncSession, page_id: UUID, page_update: PageUpdate
    ) -> Page | None:
        page: Page | None = await session.get(Page, page_id)
        if page:
            page_data = page_update.model_dump(exclude_unset=True)
            for field, value in page_data.items():
                setattr(page, field, value)
            page.update_timestamp()
            session.add(page)
            await session.commit()
            await session.refresh(page)
        return page

    @staticmethod
    async def delete_page(session: AsyncSession, page_id: UUID) -> bool:
        page = await session.get(Page, page_id)
        if page:
            await session.delete(page)
            await session.commit()
            return True
        return False
