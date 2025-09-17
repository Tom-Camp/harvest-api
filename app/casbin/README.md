# Casbin Access Control

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
# “some” means: if **any** matching policy yields allow, the request is permitted
e = some(where (p.eft == allow))

[matchers]
# ---- auxiliary matchers ----------------------------------------------------
m_admin = g(r.sub, "admin")                                # admins bypass everything

m_rbac  = g(r.sub, p.sub) &&                               \
          keyMatch(r.obj, p.obj) &&                        \
          r.act == p.act                                   # classic RBAC

m_owner = (is_owner(r.sub, r.obj) &&                       \
          (r.act == "update" || r.act == "delete"))        # owner‑only ops

# ---- final matcher (the one enforce() evaluates) -------------------------
m = m_admin || m_rbac || m_owner
```

## Default Policies

```python
DEFAULT_POLICIES = [
    # Admin permissions - full access
    ("admin", "*", "*", "allow"),
    # Moderator permissions
    ("moderator", "u:*", "read", "allow"),
    ("moderator", "u:*", "update", "allow"),
    ("moderator", "u:*", "delete", "allow"),
    ("moderator", "page", "create", "allow"),
    ("moderator", "p:*", "read", "allow"),
    ("moderator", "p:*", "update", "allow"),
    ("moderator", "p:*", "delete", "allow"),
    ("moderator", "role", "read", "allow"),
    ("moderator", "policy", "read", "allow"),
    # User permissions - basic access
    ("user", "u:*", "read", "allow"),
    ("user", "p:*", "read", "allow"),
]
```
