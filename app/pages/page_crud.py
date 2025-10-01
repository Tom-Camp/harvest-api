import time
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.logging import get_logger, log_handler
from app.pages.page_models import Page
from app.pages.page_schemas import PageCreate, PageUpdate

logger = get_logger(__name__)


class PageCRUD:
    @staticmethod
    async def create_page(
        session: AsyncSession, page: PageCreate, user_id: UUID
    ) -> Page:
        """
        Create a new page

        :param session: The SQLAlchemy asyncio AsyncSession
        :param page: The PageCreate object; pages.page_schemas.PageCreate
        :param user_id: The UUID of the user
        :return: Page
        """

        db_page = Page(**page.model_dump(), user_id=user_id)

        start = time.time()

        session.add(db_page)
        await session.commit()
        await session.refresh(db_page)

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="create_page",
            table="page",
            duration_ms=duration_ms,
            page_id=str(db_page.id),
        )
        return db_page

    @staticmethod
    async def get_page(session: AsyncSession, page_id: UUID) -> Page | None:
        """
        Get a page by ID

        :param session: The SQLAlchemy asyncio AsyncSession
        :param page_id: The UUID of the page
        :return: Page or None
        """
        return await session.get(Page, page_id)

    @staticmethod
    async def get_pages(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Page]:
        """
        Get all pages

        :param session: The SQLAlchemy asyncio AsyncSession
        :param skip: The number of pages to skip
        :param limit: The number of pages to return
        :return: Sequence[Page]
        """
        statement = select(Page).offset(skip).limit(limit)

        start = time.time()

        result = await session.execute(statement)
        pages = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_pages",
            table="page",
            duration_ms=duration_ms,
            list_length=len(pages),
        )
        return pages

    @staticmethod
    async def get_user_pages(
        session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Page]:
        """
        Get all user's pages

        :param session: The SQLAlchemy asyncio AsyncSession
        :param user_id: The UUID of the user
        :param skip: The number of pages to skip
        :param limit: The number of pages to return
        :return: Sequence[Page]
        """

        statement = (
            select(Page)
            .where(Page.__table__.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        start = time.time()

        result = await session.execute(statement)
        pages = result.scalars().all()

        duration_ms = (time.time() - start) * 1000
        log_handler.log_database_operation(
            operation="get_user_pages",
            table="page",
            duration_ms=duration_ms,
            list_length=len(pages),
        )
        return pages

    @staticmethod
    async def update_page(
        session: AsyncSession, page_id: UUID, page_update: PageUpdate
    ) -> Page | None:
        """
        Update a page by ID

        :param session: The SQLAlchemy asyncio AsyncSession
        :param page_id: The UUID of the page
        :param page_update: The PageUpdate object
        :return: Page or None
        """

        page: Page | None = await session.get(Page, page_id)
        if page:
            page_data = page_update.model_dump(exclude_unset=True)
            for field, value in page_data.items():
                setattr(page, field, value)

            start = time.time()

            session.add(page)
            await session.commit()
            await session.refresh(page)

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="update_page",
                table="page",
                duration_ms=duration_ms,
                page_id=str(page_id),
            )
        return page

    @staticmethod
    async def delete_page(session: AsyncSession, page_id: UUID) -> bool:
        """
        Delete a page by ID

        :param session: The SQLAlchemy asyncio AsyncSession
        :param page_id: The UUID of the page
        :return: bool
        """
        page = await session.get(Page, page_id)
        if page:
            start = time.time()

            await session.delete(page)
            await session.commit()

            duration_ms = (time.time() - start) * 1000
            log_handler.log_database_operation(
                operation="delete_page",
                table="page",
                duration_ms=duration_ms,
                page_id=str(page_id),
            )
            return True
        return False
