import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта: src/core/config.py → src/core → src → корень
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# Явно загружаем .env в os.environ ДО чтения переменных
load_dotenv(ENV_FILE)


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _build_database_url() -> str:
    direct = os.environ.get("DATABASE_URL")
    if direct:
        return _normalize_db_url(direct)

    connection_string = os.environ.get("POSTGRES_CONNECTION_STRING")
    if connection_string:
        return _normalize_db_url(connection_string)

    username = os.environ.get("POSTGRES_USERNAME")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = os.environ.get("POSTGRES_DATABASE_NAME")

    if all([username, password, host, database]):
        return f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"

    raise RuntimeError("Cannot determine database URL. Set DATABASE_URL or POSTGRES_* variables.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="production", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    port: int = Field(default=8000, alias="PORT")

    events_provider_base_url: str = Field(alias="EVENTS_PROVIDER_BASE_URL")
    events_provider_api_key: str = Field(alias="EVENTS_PROVIDER_API_KEY")

    sync_interval_seconds: int = Field(default=86400, alias="SYNC_INTERVAL_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_database_url() -> str:
    return _build_database_url()
