import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import uvicorn

# FastAPI админка
from telegram_bot_app.admin.admin import setup_admin
from telegram_bot_app.db.base import engine

# Telegram Bot
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
import redis.asyncio as redis

from telegram_bot_app.core.config import settings
from telegram_bot_app.core.logging_config import setup_logging

from telegram_bot_app.bot.handlers.start import router as start_router
from telegram_bot_app.bot.handlers.FSM_handlers_clean import router as booking_router
from telegram_bot_app.bot.handlers.my_appointments_hendler import router as my_appointments_router

# Настройка логирования
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ---
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render автоматически устанавливает эту переменную
# Получаем токен через property для правильной обработки
try:
    BOT_TOKEN = settings.bot_token
    WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
    WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else None
except ValueError as e:
    logger.error(f"❌ Ошибка получения токена: {e}")
    raise

# Глобальные переменные
bot_instance = None
dp = None
bot_task = None  # Только для polling режима


async def init_bot():
    """Общая инициализация бота и диспетчера"""
    global bot_instance, dp

    logger.info("📡 Подключение к Redis...")

    # Берем URL Redis из переменных окружения
    # Приоритет: UPSTASH_REDIS_URL (для Render), затем REDIS_URL, затем локальный Redis
    REDIS_URL = os.environ.get("UPSTASH_REDIS_URL") or os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Подключение через from_url (поддерживает TLS для Upstash)
    redis_client = redis.from_url(REDIS_URL, decode_responses=False)
    storage = RedisStorage(redis_client)
    logger.info("✅ Redis подключен")

    # --- Инициализация бота ---
    bot_instance = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    logger.info("✅ Бот инициализирован")

    # --- Dispatcher ---
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(my_appointments_router)
    logger.info("✅ Роутеры подключены")

    return bot_instance, dp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global bot_instance, dp, bot_task

    logger.info("🚀 Запуск приложения...")
    await init_bot()

    if RENDER_EXTERNAL_URL:
        # --- РЕЖИМ WEBHOOK (для Render) ---
        webhook_info = await bot_instance.get_webhook_info()
        if webhook_info.url != WEBHOOK_URL:
            await bot_instance.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True
            )
        logger.info(f"🌐 Бот запущен в режиме WEBHOOK. URL: {WEBHOOK_URL}")
    else:
        # --- РЕЖИМ POLLING (Локально) ---
        await bot_instance.delete_webhook(drop_pending_updates=True)
        bot_task = asyncio.create_task(dp.start_polling(bot_instance))
        logger.info("💻 Бот запущен в режиме POLLING (локально)")

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 Остановка приложения...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    if bot_instance:
        if RENDER_EXTERNAL_URL:
            await bot_instance.delete_webhook()
        await bot_instance.session.close()
    logger.info("✅ Приложение остановлено")


# Создание FastAPI приложения
app = FastAPI(
    title="Telegram Bot Admin Panel",
    lifespan=lifespan
)

# Подключение админки
setup_admin(app, engine)


# --- ЭНДПОИНТ ДЛЯ ВЕБХУКА ---
@app.post(WEBHOOK_PATH if WEBHOOK_PATH else "/webhook/disabled")
async def bot_webhook(request: Request):
    """Прием обновлений от Telegram (только для Webhook режима)"""
    if not RENDER_EXTERNAL_URL:
        return {"ok": False, "error": "Webhook not configured"}

    update = types.Update.model_validate(await request.json(), context={"bot": bot_instance})
    await dp.feed_update(bot_instance, update)
    return {"ok": True}


@app.get("/")
async def root():
    return {
        "mode": "webhook" if RENDER_EXTERNAL_URL else "polling",
        "bot_active": bot_instance is not None,
        "admin_panel": "/admin/"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot_active": bot_instance is not None}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("telegram_bot_app.main:app", host="0.0.0.0", port=port, log_level="info")