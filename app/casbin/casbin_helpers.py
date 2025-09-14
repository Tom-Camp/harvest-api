from uuid import UUID


def casbin_subject(user_id: UUID) -> str:
    return f"u:{user_id}"


def casbin_object(identifier: str, object_id: UUID) -> str:
    return f"{identifier}:{object_id}"
