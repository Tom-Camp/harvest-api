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
policies = [
    # admin – total wildcard
    ("p", "admin", "*", "*", "allow"),

    # moderator – can read/update/delete any user object
    ("p", "moderator", "u:*", "read",   "allow"),
    ("p", "moderator", "u:*", "update", "allow"),
    ("p", "moderator", "u:*", "delete", "allow"),

    # moderator – can manage any page
    ("p", "moderator", "p:*", "create", "allow"),
    ("p", "moderator", "p:*", "update", "allow"),
    ("p", "moderator", "p:*", "delete", "allow"),

    # regular user – can update/delete **their own** user record
    # we will rely on the ABAC “owner” matcher for this, so the object pattern
    # can be a wildcard; the owner check will filter it down.
    ("p", "user", "u:*", "update", "allow"),
    ("p", "user", "u:*", "delete", "allow"),
]
```
