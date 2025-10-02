from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.admin.admin_routes import admin_router
from app.auth.auth_routes import auth_router
from app.beds.bed_notes_routes import bed_note_router
from app.beds.bed_routes import bed_router
from app.casbin.casbin_config import startup_casbin
from app.gardens.garden_note_routes import garden_note_router
from app.gardens.garden_routes import garden_router
from app.logging import get_logger
from app.logging.log_config import configure_structlog
from app.logging.log_middleware import LoggingMiddleware
from app.pages.page_routes import page_router
from app.plants.plant_notes_routes import plant_note_router
from app.plants.plant_routes import plant_router
from app.users.user_routes import user_router
from app.utils import database as db
from app.utils.config import settings
from app.utils.initialize import setup_initial_admin

configure_structlog()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------- CREATE TABLES ON STARTUP ----------
    async with db.engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)

    admin_user_ids: list[UUID] = []
    async for session in db.get_db():
        admin_user = await setup_initial_admin(session=session)
        admin_user_ids.append(admin_user)
        break

    await startup_casbin(app, settings.async_database_url, admin_user_ids)
    yield

    await db.engine.dispose()


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

app.include_router(auth_router, prefix="/api", tags=["authentication", "users"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(bed_router, prefix="/api", tags=["gardens"])
app.include_router(bed_note_router, prefix="/api", tags=["gardens"])
app.include_router(garden_router, prefix="/api", tags=["gardens"])
app.include_router(garden_note_router, prefix="/api", tags=["gardens", "notes"])
app.include_router(page_router, prefix="/api", tags=["pages"])
app.include_router(plant_router, prefix="/api", tags=["gardens"])
app.include_router(plant_note_router, prefix="/api", tags=["gardens", "notes"])
app.include_router(user_router, prefix="/api", tags=["users"])


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
