from fastapi import Request


def get_casbin_manager(request: Request):
    return request.app.state.casbin_manager
