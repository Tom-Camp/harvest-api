from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.schemas.user_schemas import UserPublic
from app.utils.database import get_session

router = APIRouter()


@router.get("/users/{user_id}", response_model=UserPublic)
async def get_user(user_id: str, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    return user
