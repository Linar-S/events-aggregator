from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    port: int = Field(default=8000, alias="PORT")

    events_provider_base_url: str = Field(alias="EVENTS_PROVIDER_BASE_URL")
    events_provider_api_key: str = Field(alias="EVENTS_PROVIDER_API_KEY")

    database_url: str = Field(alias="DATABASE_URL")

    sync_interval_seconds: int = Field(default=86400, alias="SYNC_INTERVAL_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()