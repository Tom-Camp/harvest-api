import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.admin.admin_routes import admin_router
from app.auth.auth_routes import auth_router
from app.casbin.casbin_config import AsyncCasbinManager
from app.logging.log_config import configure_structlog
from app.logging.log_middleware import LoggingMiddleware
from app.pages.page_routes import page_router
from app.users.role_routes import role_router
from app.users.user_routes import user_router
from app.utils.config import settings
from app.utils.initialize import initialize_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info(">>> LIFESPAN START – creating Casbin manager")
    app.state.casbin_manager = AsyncCasbinManager()
    await app.state.casbin_manager.init()
    await initialize_data(app.state.casbin_manager)
    yield
    logging.info(">>> LIFESPAN END – closing Casbin manager")
    await app.state.casbin_manager.close()


configure_structlog()

app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    LoggingMiddleware,
    excluded_paths=["/health", "/metrics"],
    include_request_body=False,
    include_response_body=False,
)


app.include_router(auth_router, prefix="/api", tags=["authentication"])
app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(role_router, prefix="/api", tags=["roles"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(page_router, prefix="/api", tags=["pages"])


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.exception_handler(RequestValidationError)
async def custom_422_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request data",
        },
    )
