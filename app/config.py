import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Estonian Grocery Price Tracker"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database (Defaults to local SQLite if Postgres is not running)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./kliendilehed.db"
    )

    # Redis (Optional)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Storage (Local Directory Fallback if MinIO is not running)
    USE_LOCAL_STORAGE: bool = True
    LOCAL_STORAGE_DIR: str = "./static/uploads"
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin")
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "product-images"

    # Scraping Config
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    SCRAPER_DEFAULT_DELAY_SECONDS: float = 1.0
    SCRAPER_CONCURRENCY_LIMIT: int = 5
    SCRAPER_REQUEST_TIMEOUT: int = 30

settings = Settings()
