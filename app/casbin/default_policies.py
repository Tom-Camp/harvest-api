from uuid import UUID

DEFAULT_POLICIES = [
    ("admin", "*", "*", "allow"),
    ("moderator", "policy", "read", "allow"),
    ("moderator", "role", "read", "allow"),
    ("moderator", "garden", "create", "allow"),
    ("moderator", "page", "create", "allow"),
    ("moderator", "us:*", "update", "allow"),
    ("moderator", "us:*", "delete", "allow"),
    ("moderator", "pa:*", "update", "allow"),
    ("moderator", "pa:*", "delete", "allow"),
    ("authenticated", "garden", "create", "allow"),
    ("authenticated", "us:*", "read", "allow"),
    ("authenticated", "ga:*", "read", "allow"),
    ("authenticated", "pa:*", "read", "allow"),
]

DEFAULT_ADMIN_USERS: list[UUID] = []
