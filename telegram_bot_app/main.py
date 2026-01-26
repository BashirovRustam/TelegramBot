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


async def webhook_monitor_task():
    """Фоновая задача для мониторинга и восстановления webhook"""
    global WEBHOOK_URL, bot_instance
    
    if not WEBHOOK_URL or not bot_instance:
        return
        
    logger.info("🔔 Запуск монитора webhook")
    
    while True:
        try:
            await asyncio.sleep(30)  # Проверяем каждые 30 секунд
            
            webhook_info = await bot_instance.get_webhook_info()
            if webhook_info.url != WEBHOOK_URL:
                logger.warning(f"⚠️ Webhook сброшен! Текущий: {webhook_info.url}, должно быть: {WEBHOOK_URL}")
                await bot_instance.set_webhook(
                    url=WEBHOOK_URL,
                    drop_pending_updates=True
                )
                logger.info("🔄 Webhook восстановлен монитором")
            else:
                logger.debug("✅ Webhook в порядке")
                
        except Exception as e:
            logger.error(f"❌ Ошибка монитора webhook: {e}")
            await asyncio.sleep(60)  # При ошибке ждем дольше


async def init_bot():
    """Общая инициализация бота и диспетчера"""
    global bot_instance, dp

    logger.info("📡 Подключение к Redis...")

    # Берем URL Redis из переменных окружения
    # Приоритет: UPSTASH_REDIS_URL (для Render), затем REDIS_URL, затем локальный Redis
    upstash_redis_url = os.environ.get("UPSTASH_REDIS_URL")
    redis_url = os.environ.get("REDIS_URL")
    
    logger.info(f"🔍 UPSTASH_REDIS_URL: {'✅ установлен' if upstash_redis_url else '❌ не установлен'}")
    logger.info(f"🔍 REDIS_URL: {'✅ установлен' if redis_url else '❌ не установлен'}")
    
    REDIS_URL = upstash_redis_url or redis_url or "redis://localhost:6379/0"
    
    # Для Upstash Redis просто используем rediss:// URL без дополнительных параметров
    # redis-py автоматически обработает SSL для rediss://
    
    # Скрываем пароль в логах для безопасности
    safe_redis_url = REDIS_URL.split('@')[-1] if '@' in REDIS_URL else REDIS_URL
    logger.info(f"🎯 Используется Redis URL: {safe_redis_url}")

    # Подключение через from_url - redis-py автоматически обработает SSL для rediss://
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
    
    try:
        await init_bot()
        logger.info("✅ Инициализация бота завершена")
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации бота: {e}")
        raise

    if RENDER_EXTERNAL_URL:
        # --- РЕЖИМ WEBHOOK (для Render) ---
        try:
            logger.info("🔧 Настройка webhook...")
            webhook_info = await bot_instance.get_webhook_info()
            logger.info(f"📋 Текущий webhook: {webhook_info.url}")
            
            # ВСЕГДА устанавливаем webhook для надежности
            logger.info(f"🔄 Установка webhook: {WEBHOOK_URL}")
            await bot_instance.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True
            )
            logger.info("✅ Webhook установлен принудительно")
            
            # Пауза и повторная проверка
            await asyncio.sleep(2)
            webhook_info_after = await bot_instance.get_webhook_info()
            logger.info(f"🔍 Проверка после установки: {webhook_info_after.url}")
            
            if webhook_info_after.url != WEBHOOK_URL:
                logger.warning("⚠️ Webhook не установился, пробуем еще раз...")
                await bot_instance.set_webhook(
                    url=WEBHOOK_URL,
                    drop_pending_updates=True
                )
                logger.info("🔄 Повторная установка webhook завершена")
                
            logger.info(f"🌐 Бот запущен в режиме WEBHOOK. URL: {WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке webhook: {e}")
            # Не прерываем запуск приложения при ошибке webhook
            logger.warning("⚠️ Продолжаем запуск без webhook")
    else:
        # --- РЕЖИМ POLLING (Локально) ---
        await bot_instance.delete_webhook(drop_pending_updates=True)
        bot_task = asyncio.create_task(dp.start_polling(bot_instance))
        logger.info("💻 Бот запущен в режиме POLLING (локально)")

    try:
        yield
        # Фоновая задача для проверки webhook в режиме webhook
        if RENDER_EXTERNAL_URL and bot_instance:
            asyncio.create_task(webhook_monitor_task())
    except Exception as e:
        logger.error(f"❌ Ошибка во время работы приложения: {e}")
        raise

    # --- SHUTDOWN ---
    logger.info("🛑 Остановка приложения...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    if bot_instance:
        # НЕ удаляем webhook при shutdown - это сбрасывает его в Telegram
        # if RENDER_EXTERNAL_URL:
        #     await bot_instance.delete_webhook()
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

    try:
        logger.info(f"📨 Получен webhook запрос от {request.client.host}")
        update_data = await request.json()
        logger.info(f"📋 Данные обновления: {update_data.get('update_id', 'unknown')}")
        
        # Детальное логирование типа обновления
        if 'message' in update_data:
            message = update_data['message']
            user_id = message.get('from', {}).get('id', 'unknown')
            text = message.get('text', 'no text')
            logger.info(f"💬 Сообщение от пользователя {user_id}: '{text}'")
        elif 'callback_query' in update_data:
            callback = update_data['callback_query']
            user_id = callback.get('from', {}).get('id', 'unknown')
            data = callback.get('data', 'no data')
            logger.info(f"🔘 Callback от пользователя {user_id}: '{data}'")
        else:
            logger.info(f"📦 Тип обновления: {list(update_data.keys())}")
        
        update = types.Update.model_validate(update_data, context={"bot": bot_instance})
        await dp.feed_update(bot_instance, update)
        
        logger.info("✅ Webhook обработан успешно")
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/")
async def root():
    return {
        "mode": "webhook" if RENDER_EXTERNAL_URL else "polling",
        "bot_active": bot_instance is not None,
        "admin_panel": "/admin/"
    }


@app.get("/health")
async def health_check():
    status = {"status": "healthy", "bot_active": bot_instance is not None}
    return status


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("telegram_bot_app.main:app", host="0.0.0.0", port=port, log_level="warning", access_log=False)