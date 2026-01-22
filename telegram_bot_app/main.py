# """
# Объединенный main.py для запуска FastAPI (админка) + Telegram Bot
# Заменяет telegram_bot_app/main.py
# """
#
# import asyncio
# import logging
# import os
# from contextlib import asynccontextmanager
#
# from fastapi import FastAPI
# import uvicorn
#
# # FastAPI админка
# from telegram_bot_app.admin.admin import setup_admin
# from telegram_bot_app.db.base import engine
#
# # Telegram Bot
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.fsm.storage.redis import RedisStorage
# import redis.asyncio as redis
#
# from telegram_bot_app.core.config import settings
# from telegram_bot_app.core.logging_config import setup_logging
#
# from telegram_bot_app.bot.handlers.start import router as start_router
# from telegram_bot_app.bot.handlers.FSM_handlers_clean import router as booking_router
# from telegram_bot_app.bot.handlers.my_appointments_hendler import router as my_appointments_router
#
# # Настройка логирования
# setup_logging(log_level="INFO")
# logger = logging.getLogger(__name__)
#
# # Глобальные переменные для бота
# bot_instance = None
# bot_task = None
#
#
# async def start_telegram_bot():
#     """Запуск Telegram бота в фоновом режиме"""
#     global bot_instance, bot_task
#
#     try:
#         logger.info("🤖 Запуск Telegram бота...")
#
#         # Redis + FSM
#         logger.info("📡 Подключение к Redis...")
#         # Для Render.com используем переменные окружения
#         redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
#         redis_port = getattr(settings, 'REDIS_PORT', 6379)
#
#         redis_client = redis.Redis(
#             host=redis_host,
#             port=redis_port,
#             db=0,
#             decode_responses=False
#         )
#         storage = RedisStorage(redis_client)
#         logger.info("✅ Redis подключен")
#
#         # Инициализация бота
#         bot_instance = Bot(
#             token=settings.BOT_TOKEN,
#             default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
#         )
#         logger.info("✅ Бот инициализирован")
#
#         # Dispatcher
#         dp = Dispatcher(storage=storage, bot=bot_instance)
#         dp.include_router(start_router)
#         dp.include_router(booking_router)
#         dp.include_router(my_appointments_router)
#         logger.info("✅ Роутеры подключены")
#
#         # Запуск polling в фоновой задаче
#         logger.info("🚀 Запуск polling...")
#         await bot_instance.delete_webhook(drop_pending_updates=True)
#
#         # Создаем фоновую задачу для polling
#         bot_task = asyncio.create_task(dp.start_polling(bot_instance))
#         logger.info("✅ Telegram bot started successfully")
#
#     except Exception as e:
#         logger.error(f"❌ Ошибка запуска бота: {e}", exc_info=True)
#         raise
#
#
# async def stop_telegram_bot():
#     """Остановка Telegram бота"""
#     global bot_instance, bot_task
#
#     try:
#         logger.info("🛑 Остановка Telegram бота...")
#
#         if bot_task:
#             bot_task.cancel()
#             try:
#                 await bot_task
#             except asyncio.CancelledError:
#                 logger.info("Bot polling task cancelled")
#
#         if bot_instance:
#             await bot_instance.session.close()
#
#         logger.info("✅ Telegram бот остановлен")
#
#     except Exception as e:
#         logger.error(f"❌ Ошибка остановки бота: {e}", exc_info=True)
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Управление жизненным циклом приложения"""
#     # Startup
#     logger.info("🚀 Запуск приложения...")
#     await start_telegram_bot()
#     yield
#     # Shutdown
#     logger.info("🛑 Остановка приложения...")
#     await stop_telegram_bot()
#
#
# # Создание FastAPI приложения
# app = FastAPI(
#     title="Telegram Bot Admin Panel",
#     description="Админ-панель + Telegram Bot",
#     version="1.0.0",
#     lifespan=lifespan
# )
#
# # Подключение админки
# setup_admin(app, engine)
#
#
# @app.get("/")
# async def root():
#     """Главная страница"""
#     return {
#         "status": "running",
#         "service": "Telegram Bot + Admin API",
#         "bot_status": "active" if bot_task and not bot_task.done() else "inactive",
#         "admin_panel": "/admin/"
#     }
#
#
# @app.get("/health")
# async def health_check():
#     """Health check для Render.com"""
#     return {
#         "status": "healthy",
#         "bot_running": bot_task is not None and not bot_task.done()
#     }
#
#
# if __name__ == "__main__":
#     # Берем порт из переменной окружения Render, по умолчанию 8000 для локальных тестов
#     port = int(os.environ.get("PORT", 8000))
#
#     uvicorn.run(
#         "telegram_bot_app.main:app",  # Путь должен быть верным относительно корня проекта
#         host="0.0.0.0",
#         port=port,
#         log_level="info",
#         reload=False
#     )


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
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Укажите в настройках Render
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# Глобальные переменные
bot_instance = None
dp = None
bot_task = None  # Только для polling режима


async def init_bot():
    """Общая инициализация бота и диспетчера"""
    global bot_instance, dp

    # Redis + FSM
    logger.info("📡 Подключение к Redis...")
    redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
    redis_port = getattr(settings, 'REDIS_PORT', 6379)

    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=False
    )
    storage = RedisStorage(redis_client)

    # Инициализация бота
    bot_instance = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    # Dispatcher
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(my_appointments_router)

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
@app.post(WEBHOOK_PATH)
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
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("telegram_bot_app.main:app", host="0.0.0.0", port=port)