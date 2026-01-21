# Настройки проекта и переменные окружения

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 🔹 Строка подключения к БД
    # SQLite для локального теста
    # Настройки PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/Telegram_bot_DB"

    # Настройки SQLite (закомментированы)
    # DATABASE_URL = "sqlite+aiosqlite:///./telegram_bot.db"

    # 🔹 Настройки Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # 🔹 Настройки Celery
    CELERY_BROKER_URL: str = f"redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = f"redis://localhost:6379/0"

    # 🔹 Токен Telegram бота
    BOT_TOKEN: str

    # 🔹 Настройки FastAPI
    DEBUG: bool = True
    APP_NAME: str = "Task Dispatcher Bot"

    class Config:
        env_file = ".env"  # читаем переменные окружения из .env
        env_file_encoding = "utf-8"

# Создаём объект настроек, который будем импортировать в проект
settings = Settings()
