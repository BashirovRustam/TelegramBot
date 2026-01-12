# Настройки проекта и переменные окружения


from pydantic import BaseSettings


class Settings(BaseSettings):
    # 🔹 Строка подключения к БД
    # SQLite для локального теста
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # 🔹 Токен Telegram бота
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN"

    # 🔹 Настройки FastAPI
    DEBUG: bool = True
    APP_NAME: str = "Task Dispatcher Bot"

    class Config:
        env_file = ".env"  # читаем переменные окружения из .env
        env_file_encoding = "utf-8"


# Создаём объект настроек, который будем импортировать в проект
settings = Settings()
