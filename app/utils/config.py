from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Harvesting.Food"
    ACCESS_TOKEN_EXPIRE_MINUTES: float = 30
    CORS_ORIGINS: List[str] | None = None
    DB_USER: str | None = None
    DB_PASS: str | None = None
    ENVIRONMENT: str | None = None
    HASH_ALGORITHM: str | None = None
    INITIAL_USER_NAME: str = "admin"
    INITIAL_USER_MAIL: str = "admin@example.com"
    INITIAL_USER_PASS: str = "Ch4ng3M3!"
    LOG_LEVEL: str = "INFO"
    LOG_NAME: str = "harvestLog"
    LOG_JSON_FORMAT: bool = False
    LOG_ACCESS_NAME: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PASS: str | None = None
    POSTGRES_PORT: str | None = None
    POSTGRES_USER: str | None = None
    SECRET_KEY: str | None = None
    USER_SECRET: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def postgres_uri(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASS}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
