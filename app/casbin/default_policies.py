from typing import List
from uuid import UUID

DEFAULT_POLICIES = [
    ("admin", "*", "*", "allow"),
    ("moderator", "u:*", "read", "allow"),
    ("moderator", "u:*", "update", "allow"),
    ("moderator", "u:*", "delete", "allow"),
    ("moderator", "garden", "create", "allow"),
    ("moderator", "page", "create", "allow"),
    ("moderator", "p:*", "read", "allow"),
    ("moderator", "p:*", "update", "allow"),
    ("moderator", "p:*", "delete", "allow"),
    ("moderator", "role", "read", "allow"),
    ("moderator", "policy", "read", "allow"),
    ("authenticated", "garden", "create", "allow"),
    ("authenticated", "u:*", "read", "allow"),
    ("authenticated", "p:*", "read", "allow"),
]

DEFAULT_ADMIN_USERS: List[UUID] = []
