from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = "SyncBoard"
    DEBUG: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme-super-secret-key-32chars!!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://syncboard:syncboard@localhost:5432/syncboard"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Add FRONTEND_URL env var on Render to allow your frontend domain
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:80",
        os.getenv("FRONTEND_URL", "https://syncboard-frontend.onrender.com"),
    ]

    WS_HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
