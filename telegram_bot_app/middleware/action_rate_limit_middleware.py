"""
Middleware для проверки rate limits на уровне aiogram
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

import redis.asyncio as redis

from telegram_bot_app.middleware.rate_limit_service import RateLimitService
from telegram_bot_app.middleware.rate_limit_config import RateLimitConfig

logger = logging.getLogger(__name__)


class ActionRateLimitMiddleware(BaseMiddleware):
    """
    Middleware для контроля частоты действий пользователя
    
    Работает на уровне callback_query и message handlers.
    Проверяет лимиты для конкретных действий (создание записи, отмена и т.д.)
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Args:
            redis_client: Асинхронный клиент Redis
        """
        super().__init__()
        self.rate_limit_service = RateLimitService(redis_client)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Основной метод middleware
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Событие (Message или CallbackQuery)
            data: Контекст данных
            
        Returns:
            Результат выполнения handler или None если лимит превышен
        """
        # Определяем, какое действие пытается выполнить пользователь
        action = self._detect_action(event, data)
        
        # Если действие не требует проверки лимита - пропускаем
        if action is None:
            return await handler(event, data)
        
        # Получаем ID пользователя
        user_id = self._get_user_id(event)
        if user_id is None:
            logger.warning("Could not extract user_id from event")
            return await handler(event, data)
        
        # Проверяем лимит
        is_allowed, retry_after = await self.rate_limit_service.check_rate_limit(
            user_id=user_id,
            action=action
        )
        
        if not is_allowed:
            # Лимит превышен - отправляем сообщение пользователю
            logger.warning(
                f"Rate limit exceeded for user {user_id}, action {action}. "
                f"Retry after {retry_after}s"
            )
            await self._send_rate_limit_message(event, action, retry_after)
            return None
        
        # Лимит не превышен - выполняем handler
        result = await handler(event, data)
        
        # После успешного выполнения увеличиваем счетчик
        # ВАЖНО: увеличиваем только после успешного выполнения handler
        await self.rate_limit_service.increment_counter(user_id, action)
        
        return result
    
    def _detect_action(self, event: TelegramObject, data: Dict[str, Any]) -> str | None:
        """
        Определяет, какое действие пытается выполнить пользователь
        
        Args:
            event: Событие Telegram
            data: Контекст данных
            
        Returns:
            str | None: Название действия или None если не требует проверки
        """
        # Для CallbackQuery проверяем callback_data
        if isinstance(event, CallbackQuery):
            callback_data = event.data
            
            # Подтверждение создания записи
            if callback_data and callback_data.startswith("confirm_booking:confirm"):
                return RateLimitConfig.CREATE_APPOINTMENT
            
            # Отмена записи
            if callback_data and callback_data.startswith("cancel_appointment:"):
                return RateLimitConfig.CANCEL_APPOINTMENT
        
        # Для Message можно добавить проверки по тексту
        # elif isinstance(event, Message):
        #     # Пример: если пользователь отправляет текстовую команду
        #     pass
        
        # Действие не требует проверки лимита
        return None
    
    def _get_user_id(self, event: TelegramObject) -> int | None:
        """
        Извлекает user_id из события
        
        Args:
            event: Событие Telegram
            
        Returns:
            int | None: ID пользователя
        """
        if isinstance(event, CallbackQuery):
            return event.from_user.id
        elif isinstance(event, Message):
            return event.from_user.id
        return None
    
    async def _send_rate_limit_message(
        self, 
        event: TelegramObject, 
        action: str, 
        retry_after: int
    ) -> None:
        """
        Отправляет сообщение о превышении лимита
        
        Args:
            event: Событие Telegram
            action: Название действия
            retry_after: Через сколько секунд можно повторить
        """
        error_message = RateLimitConfig.get_error_message(action, retry_after)
        
        try:
            if isinstance(event, CallbackQuery):
                # Для callback показываем alert
                await event.answer(
                    text=f"⏳ Превышен лимит. Попробуйте через {retry_after // 60} мин.",
                    show_alert=True
                )
                # Также отправляем полное сообщение в чат
                if event.message:
                    await event.message.answer(error_message)
            elif isinstance(event, Message):
                await event.answer(error_message)
        except Exception as e:
            logger.error(f"Error sending rate limit message: {e}", exc_info=True)


class RateLimitStatsMiddleware(BaseMiddleware):
    """
    Вспомогательный middleware для логирования статистики (опционально)
    Можно использовать для отладки и мониторинга
    """
    
    def __init__(self, redis_client: redis.Redis):
        super().__init__()
        self.rate_limit_service = RateLimitService(redis_client)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Логирует статистику по лимитам перед обработкой"""
        
        user_id = None
        if isinstance(event, (CallbackQuery, Message)):
            user_id = event.from_user.id
        
        if user_id:
            stats = await self.rate_limit_service.get_user_stats(user_id)
            logger.debug(f"Rate limit stats for user {user_id}: {stats}")
        
        return await handler(event, data)
