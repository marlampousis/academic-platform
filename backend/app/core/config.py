from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Email
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str | None = None
    EMAIL_PASSWORD: str | None = None
    EMAIL_FROM: str | None = None
    EMAIL_FROM_NAME: str = "Academic Platform"
    EMAIL_USE_TLS: bool = True
    EMAIL_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
