from typing import Any
from uuid import UUID


def casbin_subject(user_id: UUID) -> str:
    return f"user:{user_id}"


def casbin_object(kind: str, object_id: UUID) -> str:
    # kind = "u" for user, "p" for page, etc.
    return f"{kind}:{object_id}"


def is_owner(subject_id: str, check_object: Any) -> bool:
    """
    Return True if `subject_id` (e.g., "user:1234") is the owner of `check_object`.

    `check_object` can be:
      * a Page instance (has .user_id)
      * a User instance (owner is the user itself)
      * any other domain object that defines an `user_id` association.
      * a string in format "kind:uuid" (e.g., "p:uuid" or "u:uuid")
    """
    try:
        _, sub_uuid = subject_id.split(":")
    except (ValueError, AttributeError):
        return False

    # Check if the object has a user_id attribute (like Page instances)
    if hasattr(check_object, "user_id") and check_object.user_id:
        return str(check_object.user_id) == sub_uuid

    # Check if the object is a User instance itself
    if hasattr(check_object, "id") and not hasattr(check_object, "user_id"):
        return str(check_object.id) == sub_uuid

    # Handle string format objects like "p:uuid" or "u:uuid"
    if isinstance(check_object, str):
        try:
            kind, oid = check_object.split(":")
        except ValueError:
            return False

        # For user objects, check if it's the same user
        if kind == "u":
            return oid == sub_uuid

        # For page objects, we cannot determine ownership from string alone
        # This should be handled by passing the actual object instance
        # or by implementing a database lookup
        if kind == "p":
            # TODO: Implement page ownership lookup
            # For now, return False - this should be replaced with actual logic
            # that queries the database to check if the user owns the page
            return False

    return False


def can_access_page(subject_id: str, page_obj: Any) -> bool:
    """
    Helper function to check if a user can access a specific page.
    This should be used for page-specific ownership checks.
    """
    return is_owner(subject_id, page_obj)
