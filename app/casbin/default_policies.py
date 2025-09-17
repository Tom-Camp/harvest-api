from typing import List
from uuid import UUID

DEFAULT_POLICIES = [
    ("admin", "*", "*"),
    ("admin", "role", "add"),
    ("admin", "role", "delete"),
    ("admin", "role", "read"),
    ("admin", "policy", "read"),
    ("admin", "policy", "add"),
    ("moderator", "u:*", "read"),
    ("moderator", "u:*", "update"),
    ("moderator", "u:*", "delete"),
    ("moderator", "page", "create"),
    ("moderator", "p:*", "read"),
    ("moderator", "p:*", "update"),
    ("moderator", "p:*", "delete"),
    ("moderator", "role", "read"),
    ("moderator", "policy", "read"),
    ("authenticated", "u:*", "read"),
    ("authenticated", "page", "create"),
    ("authenticated", "p:*", "read"),
]

DEFAULT_ADMIN_USERS: List[UUID] = []
