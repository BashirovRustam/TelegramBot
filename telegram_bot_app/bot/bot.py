import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

import redis.asyncio as redis

from telegram_bot_app.core.config import settings
from telegram_bot_app.core.logging_config import setup_logging

from telegram_bot_app.bot.handlers.start import router as start_router
from telegram_bot_app.bot.handlers.FSM_handlers_clean import router as booking_router
from telegram_bot_app.bot.handlers.my_appointments_hendler import router as my_appointments_router

# Импортируем планировщик
from telegram_bot_app.scheduler.background_scheduler import AppointmentNotificationScheduler

logger = logging.getLogger(__name__)

# Глобальная переменная для планировщика
notification_scheduler = None


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    global notification_scheduler

    logger.info("🚀 Bot startup sequence initiated...")

    try:
        # Создаем и запускаем планировщик уведомлений за 1 час до записи
        notification_scheduler = AppointmentNotificationScheduler(
            bot=bot,
            check_interval_minutes=5,  # Проверяем каждые 5 минут
            notify_hours_before=1  # Уведомляем за 1 час
        )
        await notification_scheduler.start()

        logger.info("✅ Background notification scheduler started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    global notification_scheduler

    logger.info("🛑 Bot shutdown sequence initiated...")

    try:
        if notification_scheduler:
            await notification_scheduler.stop()

        logger.info("✅ Background scheduler stopped successfully")

    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}", exc_info=True)


async def main():
    # =========================
    # 1️⃣ ЛОГИРОВАНИЕ
    # =========================
    setup_logging(log_level="INFO")
    logger.info("🤖 Запуск Telegram бота...")

    try:
        # =========================
        # 2️⃣ REDIS + FSM
        # =========================
        logger.info("📡 Подключение к Redis...")

        # Берем URL Redis из переменных окружения
        # Приоритет: UPSTASH_REDIS_URL (для Render), затем REDIS_URL, затем локальный Redis
        upstash_redis_url = os.environ.get("UPSTASH_REDIS_URL")
        redis_url = os.environ.get("REDIS_URL")
        
        logger.info(f"🔍 UPSTASH_REDIS_URL: {'✅ установлен' if upstash_redis_url else '❌ не установлен'}")
        logger.info(f"🔍 REDIS_URL: {'✅ установлен' if redis_url else '❌ не установлен'}")
        
        REDIS_URL = upstash_redis_url or redis_url or "redis://localhost:6379/0"
        
        # Скрываем пароль в логах для безопасности
        safe_redis_url = REDIS_URL.split('@')[-1] if '@' in REDIS_URL else REDIS_URL
        logger.info(f"🎯 Используется Redis URL: {safe_redis_url}")

        # Подключение через from_url
        redis_client = redis.from_url(REDIS_URL, decode_responses=False)
        storage = RedisStorage(redis_client)
        logger.info("✅ Redis подключен")

        # =========================
        # 3️⃣ BOT
        # =========================
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        logger.info("✅ Бот инициализирован")

        # =========================
        # 4️⃣ DISPATCHER
        # =========================
        dp = Dispatcher(storage=storage, bot=bot)

        # Регистрируем роутеры
        dp.include_router(start_router)
        dp.include_router(booking_router)
        dp.include_router(my_appointments_router)

        logger.info("✅ Роутеры подключены")

        # =========================
        # 5️⃣ STARTUP/SHUTDOWN HOOKS
        # =========================
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        logger.info("✅ Lifecycle hooks registered")

        # =========================
        # 6️⃣ POLLING
        # =========================
        logger.info("🚀 Запуск polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.critical(
            "❌ Критическая ошибка при запуске бота",
            exc_info=True
        )
        raise
    finally:
        # Закрываем соединение с Redis
        if 'redis_client' in locals():
            await redis_client.close()
            logger.info("✅ Redis connection closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен пользователем")