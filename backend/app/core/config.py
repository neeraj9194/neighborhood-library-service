from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgres://library_user:library_pass@db:5432/library_db"

    # Application
    APP_NAME: str = "Neighborhood Library Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Borrowing defaults
    DEFAULT_BORROW_DAYS: int = 14

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
