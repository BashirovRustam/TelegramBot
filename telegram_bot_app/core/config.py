import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Загружаем .env файл для локальной разработки
load_dotenv()

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/Telegram_bot_DB"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    CELERY_BROKER_URL: str = f"redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = f"redis://localhost:6379/0"

    # Telegram Bot token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

    # 2GIS API
    TWOGIS_API_KEY: Optional[str] = None

    @property
    def twogis_api_key(self):
        return self.TWOGIS_API_KEY or os.getenv("2GIS_API_KEY")

    # FastAPI
    DEBUG: bool = True
    APP_NAME: str = "Task Dispatcher Bot"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
