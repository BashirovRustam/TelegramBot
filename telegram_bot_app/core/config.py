import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator

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
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Telegram Bot token - теперь Optional с валидатором
    BOT_TOKEN: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # 2GIS API
    TWOGIS_API_KEY: Optional[str] = None

    # FastAPI
    DEBUG: bool = True
    APP_NAME: str = "Task Dispatcher Bot"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator('DATABASE_URL', mode='after')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Преобразует postgresql:// в postgresql+asyncpg://"""
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def bot_token(self) -> str:
        """Получает BOT_TOKEN из переменных окружения"""
        token = self.BOT_TOKEN or self.TELEGRAM_BOT_TOKEN or os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN or TELEGRAM_BOT_TOKEN must be set in environment variables")
        return token

    @property
    def twogis_api_key(self) -> Optional[str]:
        """Получает 2GIS API ключ из переменных окружения"""
        return self.TWOGIS_API_KEY or os.getenv("2GIS_API_KEY")

settings = Settings()