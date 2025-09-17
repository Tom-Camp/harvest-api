from typing import List

from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = Field(default="Harvesting.Food")
    ACCESS_TOKEN_EXPIRE_MINUTES: float = 30
    CASBIN_DB_URL: str | None = None
    CORS_ORIGINS: List[str] | None = None
    ENVIRONMENT: str | None = None
    HASH_ALGORITHM: str | None = None
    INITIAL_USER_NAME: str = Field(default="admin")
    INITIAL_USER_MAIL: str = Field(default="admin@example.com")
    INITIAL_USER_PASS: str = Field(default="Ch4ng3M3!")
    LOG_LEVEL: str = Field(default="INFO")
    LOG_NAME: str = Field(default="harvestLog")
    LOG_JSON_FORMAT: bool = False
    LOG_ACCESS_NAME: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PASS: SecretStr = Field(default="postgres")
    POSTGRES_PORT: str | None = None
    POSTGRES_USER: str | None = None
    SECRET_KEY: str | None = None
    SITE_EMAIL: EmailStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def async_database_url(self) -> str:
        pwd = self.POSTGRES_PASS.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{pwd}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
