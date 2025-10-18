from uuid import UUID

from fastapi import HTTPException

from app.core.auth.scopes_manager import ScopesManager
from app.logging import get_logger
from app.schemas.auth_schemas import TokenData

logger = get_logger(__name__)


def check_garden_access(current_user: TokenData, garden_user: UUID, scope: str):

    access_any = ScopesManager.has_scope(
        user_scopes=current_user.scopes, required_scope=scope
    )
    is_owner = ScopesManager.is_owner(
        user_scopes=current_user.scopes,
        required_scope=f"{scope}:own",
        user_id=current_user.id,
        entity_owner=garden_user,
    )

    if not access_any and not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")
