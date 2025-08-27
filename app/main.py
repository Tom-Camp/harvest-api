import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_users import FastAPIUsers
from fastapi_users.password import PasswordHelper

from app.auth import auth_backend
from app.config import settings
from app.database import Base, async_session, engine
from app.models.user_manager import get_user_manager

# from app.models.garden import Plant
from app.models.users import User, UserCreate, UserRead, UserUpdate

# from app.routes import garden_routes


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        new_engine = await init_db()
        app.state.async_session = async_session
        print("Connected to PostgreSQL. Database is ready.")

        async def create_db_and_tables():
            async with new_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            from sqlalchemy import select

            stmt = select(User).where(User.email == settings.initial_user_mail)
            result = await session.execute(stmt)
            default_user = result.scalar_one_or_none()

            if not default_user:
                password_helper = PasswordHelper()
                new_user = User(
                    email=settings.initial_user_mail,
                    hashed_password=password_helper.hash(settings.initial_user_pass),
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                print(f"Created default user: {new_user.id}: {new_user.email}")
            else:
                print(f"Default user {settings.initial_user_mail} already exists")
        yield
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        if "engine" in locals():
            await new_engine.dispose()
            print("Closed PostgreSQL connection")


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
)

origins = ["http://localhost:8080", "https://tom.camp"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(garden_routes.router, prefix="/api")

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)


app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


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
