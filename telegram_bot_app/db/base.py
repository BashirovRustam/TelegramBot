# app/db/base.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from telegram_bot_app.core.config import settings  # читаем DATABASE_URL из config.py

# 1️⃣ Base для всех моделей
class Base(DeclarativeBase):
    pass

# 2️⃣ Engine — для async SQLite
engine = create_async_engine(
    settings.DATABASE_URL,  # DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    echo=True,               # для логов SQL запросов
    future=True
)

# 3️⃣ Session — фабрика сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4️⃣ Зависимость для FastAPI
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
