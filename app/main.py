from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.v1.admin_routes import admin_router
from app.api.v1.auth_routes import auth_router
from app.api.v1.bed_notes_routes import bed_note_router
from app.api.v1.bed_routes import bed_router
from app.api.v1.garden_note_routes import garden_note_router
from app.api.v1.garden_routes import garden_router
from app.api.v1.page_routes import page_router
from app.api.v1.plant_notes_routes import plant_note_router
from app.api.v1.plant_routes import plant_router
from app.api.v1.user_routes import user_router
from app.core.utils import database as db
from app.core.utils.config import settings
from app.core.utils.initialize import setup_initial_admin
from app.logging import get_logger
from app.logging.log_config import configure_structlog
from app.logging.log_middleware import LoggingMiddleware

configure_structlog()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------- CREATE TABLES ON STARTUP ----------
    async with db.engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)

    await setup_initial_admin()
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
