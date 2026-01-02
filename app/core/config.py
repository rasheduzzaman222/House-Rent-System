from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# -------------------- PROJECT ROOT --------------------

BASE_DIR = Path(__file__).resolve().parents[2]


# -------------------- SETTINGS --------------------

class Settings(BaseSettings):
    # -------------------- DATABASE --------------------
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/house_rent_db"

    # -------------------- SECURITY --------------------
    SECRET_KEY: str = "dev-secret-key-change-this"
    SESSION_COOKIE_NAME: str = "house_rent_session"

    # -------------------- Pydantic v2 config --------------------
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# -------------------- CACHED SETTINGS --------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
