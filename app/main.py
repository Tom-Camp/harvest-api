from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.garden import Plant
from app.routes import garden_routes


async def init_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=[Plant],
    )
    return client


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client = await init_db()
        print(f"Connected to MongoDB. Database '{settings.mongo_db}' is ready.")
        yield
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        if "client" in locals():
            client.close()
            print("Closed MongoDB connection")


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

app.include_router(garden_routes.router, prefix="/api")


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
