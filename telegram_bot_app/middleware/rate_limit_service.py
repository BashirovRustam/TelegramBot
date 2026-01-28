"""
Сервис для работы с rate limiting через Redis
"""
import logging
from typing import Optional, Tuple
from datetime import datetime

import redis.asyncio as redis

from telegram_bot_app.middleware.rate_limit_config import RateLimitConfig

logger = logging.getLogger(__name__)


class RateLimitService:
    """Сервис для проверки и управления лимитами запросов"""
    
    def __init__(self, redis_client: redis.Redis):
        """
        Args:
            redis_client: Асинхронный клиент Redis
        """
        self.redis = redis_client
        self.prefix = "rate_limit"
    
    def _get_key(self, user_id: int, action: str) -> str:
        """
        Генерирует ключ для Redis
        
        Args:
            user_id: ID пользователя
            action: Название действия
            
        Returns:
            str: Ключ вида "rate_limit:user:123:create_appointment"
        """
        return f"{self.prefix}:user:{user_id}:{action}"
    
    async def check_rate_limit(
        self, 
        user_id: int, 
        action: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Проверяет, не превышен ли лимит для пользователя
        
        Args:
            user_id: ID пользователя
            action: Название действия (из RateLimitConfig)
            
        Returns:
            Tuple[bool, Optional[int]]: 
                - True если можно выполнить действие, False если лимит превышен
                - Количество секунд до сброса лимита (None если можно выполнить)
        """
        try:
            limit_config = RateLimitConfig.get_limit(action)
            key = self._get_key(user_id, action)
            
            # Получаем текущее количество запросов
            current_count = await self.redis.get(key)
            
            if current_count is None:
                # Первый запрос - разрешаем
                logger.debug(f"First request for user {user_id}, action {action}")
                return True, None
            
            current_count = int(current_count)
            
            # Проверяем лимит
            if current_count >= limit_config.max_requests:
                # Лимит превышен - получаем TTL
                ttl = await self.redis.ttl(key)
                logger.warning(
                    f"Rate limit exceeded for user {user_id}, action {action}. "
                    f"Count: {current_count}/{limit_config.max_requests}, TTL: {ttl}s"
                )
                return False, ttl if ttl > 0 else limit_config.window_seconds
            
            # Лимит не превышен
            logger.debug(
                f"Rate limit OK for user {user_id}, action {action}. "
                f"Count: {current_count}/{limit_config.max_requests}"
            )
            return True, None
            
        except KeyError as e:
            logger.error(f"Unknown action: {action}. Error: {e}")
            # В случае неизвестного действия - разрешаем
            return True, None
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}", exc_info=True)
            # В случае ошибки Redis - разрешаем (fail-open)
            return True, None
    
    async def increment_counter(self, user_id: int, action: str) -> int:
        """
        Увеличивает счетчик запросов для пользователя
        
        Args:
            user_id: ID пользователя
            action: Название действия
            
        Returns:
            int: Новое значение счетчика
        """
        try:
            limit_config = RateLimitConfig.get_limit(action)
            key = self._get_key(user_id, action)
            
            # Используем pipeline для атомарности
            async with self.redis.pipeline() as pipe:
                # INCR увеличивает счетчик (создает если не существует)
                await pipe.incr(key)
                # Устанавливаем TTL только если это первый запрос
                await pipe.expire(key, limit_config.window_seconds, nx=True)
                results = await pipe.execute()
            
            new_count = results[0]
            
            logger.info(
                f"Incremented rate limit counter for user {user_id}, action {action}. "
                f"New count: {new_count}/{limit_config.max_requests}"
            )
            
            return new_count
            
        except Exception as e:
            logger.error(f"Error incrementing counter: {e}", exc_info=True)
            return 0
    
    async def reset_limit(self, user_id: int, action: str) -> bool:
        """
        Сбрасывает лимит для пользователя (для админов/отладки)
        
        Args:
            user_id: ID пользователя
            action: Название действия
            
        Returns:
            bool: True если успешно сброшено
        """
        try:
            key = self._get_key(user_id, action)
            await self.redis.delete(key)
            
            logger.info(f"Reset rate limit for user {user_id}, action {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting limit: {e}", exc_info=True)
            return False
    
    async def get_remaining_requests(self, user_id: int, action: str) -> Tuple[int, int]:
        """
        Получает количество оставшихся запросов
        
        Args:
            user_id: ID пользователя
            action: Название действия
            
        Returns:
            Tuple[int, int]: (оставшиеся запросы, всего разрешено)
        """
        try:
            limit_config = RateLimitConfig.get_limit(action)
            key = self._get_key(user_id, action)
            
            current_count = await self.redis.get(key)
            current_count = int(current_count) if current_count else 0
            
            remaining = max(0, limit_config.max_requests - current_count)
            
            return remaining, limit_config.max_requests
            
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}", exc_info=True)
            return 0, 0
    
    async def get_user_stats(self, user_id: int) -> dict:
        """
        Получает статистику по всем действиям пользователя (для отладки)
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Статистика по действиям
        """
        stats = {}
        
        for action in RateLimitConfig.LIMITS.keys():
            try:
                key = self._get_key(user_id, action)
                count = await self.redis.get(key)
                ttl = await self.redis.ttl(key)
                limit_config = RateLimitConfig.get_limit(action)
                
                stats[action] = {
                    'current': int(count) if count else 0,
                    'limit': limit_config.max_requests,
                    'ttl_seconds': ttl if ttl > 0 else 0,
                    'window_seconds': limit_config.window_seconds
                }
            except Exception as e:
                logger.error(f"Error getting stats for action {action}: {e}")
                stats[action] = {'error': str(e)}
        
        return stats
