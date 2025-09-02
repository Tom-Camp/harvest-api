from fastapi import APIRouter, Depends

from app.models.users import User
from app.schemas.auth_schemas import Token
from app.schemas.user_schemas import UserRead
from app.utils.auth import get_current_active_user, login_for_access_token

router = APIRouter()


@router.post("/token", response_model=Token)
async def issue_token(token: Token = Depends(login_for_access_token)):
    return token


@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
