from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Harvesting.Food"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    CORS_ORIGINS: List[str]
    DB_USER: str
    DB_PASS: str
    ENVIRONMENT: str
    HASH_ALGORITHM: str
    INITIAL_USER_NAME: str
    INITIAL_USER_MAIL: str
    INITIAL_USER_PASS: str
    LOG_LEVEL: str = "INFO"
    LOG_JSON_FORMAT: bool = False
    LOG_NAME: str
    LOG_ACCESS_NAME: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PASS: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    SECRET_KEY: str
    USER_SECRET: str

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
