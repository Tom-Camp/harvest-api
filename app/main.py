from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import select

# from app.models.garden import Plant
from app.models.users import User
from app.utils.config import settings
from app.utils.database import AsyncSessionLocal, async_engine, create_db_and_tables
from app.utils.initialize import initial_user

# from app.routes import garden_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_db_and_tables()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == settings.initial_user_mail)
            )
            user = result.scalar_one_or_none()
            if not user:
                role, new_user = initial_user()
                session.add(role)
                session.add(new_user)
                await session.commit()
        yield
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        await async_engine.dispose()
        print("Closed PostgreSQL connection")


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

# app.include_router(
#     fastapi_users.get_auth_router(auth_backend),
#     prefix="/auth/jwt",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_register_router(UserRead, UserCreate),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_verify_router(UserRead),
#     prefix="/auth",
#     tags=["auth"],
# )
#
# app.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/users",
#     tags=["users"],
# )


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
