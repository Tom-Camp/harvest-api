# Casbin Access Control

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g  = _, _          # user → role
g2 = _, _          # role → role (inheritance, optional)

[functions]
# Name used inside the matcher → actual Python callable registered in code
is_owner = is_owner

[policy_effect]
# “some” means: if **any** matching policy yields allow, the request is permitted
e = some(where (p.eft == allow))

[matchers]
# ---- auxiliary matchers ----------------------------------------------------
m_admin = g(r.sub, "admin")                                 # admins bypass everything

m_rbac  = g(r.sub, p.sub) &&                               \
          keyMatch2(r.obj, p.obj) &&                        \
          r.act == p.act                                      # classic RBAC

m_owner = is_owner(r.sub, r.obj) &&                         \
          (r.act == "update" || r.act == "delete")           # owner‑only ops

# ---- final matcher (the one enforce() evaluates) -------------------------
m = m_admin || m_rbac || m_owner
```

## Default Policies

```python
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
```
