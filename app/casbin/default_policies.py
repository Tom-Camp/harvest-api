from typing import List
from uuid import UUID

DEFAULT_POLICIES = [
    # Admin permissions - full access
    ("admin", "*", "*"),
    ("admin", "role", "add"),
    ("admin", "role", "delete"),
    ("admin", "role", "read"),
    ("admin", "policy", "read"),
    # Moderator permissions
    ("moderator", "u:*", "read"),
    ("moderator", "u:*", "update"),
    ("moderator", "u:*", "delete"),
    ("moderator", "p:*", "create"),
    ("moderator", "p:*", "read"),
    ("moderator", "p:*", "update"),
    ("moderator", "p:*", "delete"),
    ("moderator", "role", "read"),
    ("moderator", "policy", "read"),
    # User permissions - basic access
    ("user", "u:*", "read"),
    ("user", "p:*", "create"),
    ("user", "p:*", "read"),
]

DEFAULT_ADMIN_USERS: List[UUID] = []
