from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import select

from app.models.users import User
from app.routes import auth_routes, user_routes
from app.utils.config import settings
from app.utils.database import get_session, init_db
from app.utils.initialize import initial_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.email == settings.initial_user_mail)
        )
        user = result.scalar_one_or_none()
        if user is None:
            role, user = initial_user()
            session.add(role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        break
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
)

origins = ["http://localhost:5000", "https://tom.camp"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(user_routes.router, prefix="/api", tags=["user"])


@app.get("/health")
async def health():
    return {"status": "ok"}


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
