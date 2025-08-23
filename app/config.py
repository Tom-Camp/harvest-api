from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tom.Camp"
    mongo_db: str
    mongo_host: str
    mongo_pass: str
    mongo_port: str
    mongo_user: str
    db_user: str
    db_pass: str
    secret_key: str
    hash_algorithm: str
    initial_user_name: str
    initial_user_mail: str
    initial_user_pass: str
    hf_agent: str
    hf_model: str
    hf_token: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def mongodb_uri(self):
        return (
            f"mongodb://{self.db_user}:{self.db_pass}@{self.mongo_host}:"
            f"{self.mongo_port}/{self.mongo_db}?authSource={self.mongo_db}"
        )


settings = Settings()
