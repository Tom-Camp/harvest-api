from typing import List, Optional

from sqlmodel import Session, select

from app.models.users import User
from app.schemas.users_schemas import UserCreate, UserUpdate


class UserCRUD:
    @staticmethod
    async def create(session: Session, user_data: UserCreate) -> User:
        user = User(**user_data.model_dump())
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    async def get(session: Session, user_id: str) -> Optional[User]:
        return session.get(User, user_id)

    @staticmethod
    async def get_by_email(session: Session, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

    @staticmethod
    async def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
        statement = select(User).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    async def update(
        session: Session, user_id: str, user_data: UserUpdate
    ) -> Optional[User]:
        user = session.get(User, user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.update_timestamp()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    async def delete(session: Session, user_id: str) -> bool:
        user = session.get(User, user_id)
        if not user:
            return False

        session.delete(user)
        session.commit()
        return True
