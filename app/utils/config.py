from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tom.Camp"
    access_token_expire_minutes: str
    db_user: str
    db_pass: str
    hash_algorithm: str
    initial_user_name: str
    initial_user_mail: str
    initial_user_pass: str
    postgres_db: str
    postgres_host: str
    postgres_pass: str
    postgres_port: str
    postgres_user: str
    secret_key: str
    user_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def postgres_uri(self):
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_pass}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
