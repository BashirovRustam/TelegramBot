# import asyncio
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.fsm.storage.redis import RedisStorage
# import redis.asyncio as redis
# from telegram_bot_app.core.config import settings
# from telegram_bot_app.bot.handlers.start import router as start_router
# from telegram_bot_app.bot.handlers.FSM_handlers_clean import router as booking_router  # импорт FSM router
# from telegram_bot_app.bot.handlers.my_appointments_hendler import router as my_appointments_router
#
#
# async def main():
#     # 🔹 Подключаем Redis для FSM
#     redis_client = redis.Redis(host="localhost", port=6379, db=0)
#     storage = RedisStorage(redis_client)
#
#     # 🔹 Инициализация бота с Markdown
#     bot = Bot(
#         token=settings.BOT_TOKEN,
#         default=DefaultBotProperties(
#             parse_mode=ParseMode.MARKDOWN
#         )
#     )
#
#     # 🔹 Диспетчер с подключенным FSM storage
#     dp = Dispatcher(storage=storage, bot=bot)
#
#     # 🔹 Роутеры
#     dp.include_router(start_router)       # обычные команды /start и т.д.
#     dp.include_router(booking_router)     # FSM для "Создать запись"
#     dp.include_router(my_appointments_router)  # Handler для "Мои записи"
#
#     # 🔹 Удаляем старые вебхуки (если были) и стартуем polling
#     await bot.delete_webhook(drop_pending_updates=True)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())






import asyncio
import logging

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


logger = logging.getLogger(__name__)


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
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
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

        dp.include_router(start_router)
        dp.include_router(booking_router)
        dp.include_router(my_appointments_router)

        logger.info("✅ Роутеры подключены")

        # =========================
        # 5️⃣ POLLING
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен пользователем")












