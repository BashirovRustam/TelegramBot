"""
Конфигурация лимитов для действий пользователей
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class RateLimit:
    """Конфигурация лимита для конкретного действия"""
    max_requests: int  # Максимальное количество запросов
    window_seconds: int  # Окно времени в секундах
    
    @property
    def window_hours(self) -> float:
        """Получить окно в часах для отображения"""
        return self.window_seconds / 3600


class RateLimitConfig:
    """Централизованная конфигурация всех лимитов"""
    
    # Действия, которые мы хотим лимитировать
    CREATE_APPOINTMENT = "create_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    
    # Определяем лимиты для каждого действия
    LIMITS: Dict[str, RateLimit] = {
        # Создание записи: 3 записи в час
        CREATE_APPOINTMENT: RateLimit(
            max_requests=3,
            window_seconds=3600  # 1 час
        ),
        
        # Отмена записи: 5 отмен в час (более мягкий лимит)
        CANCEL_APPOINTMENT: RateLimit(
            max_requests=5,
            window_seconds=3600  # 1 час
        ),
    }
    
    @classmethod
    def get_limit(cls, action: str) -> RateLimit:
        """
        Получить лимит для действия
        
        Args:
            action: Название действия
            
        Returns:
            RateLimit: Конфигурация лимита
            
        Raises:
            KeyError: Если действие не найдено
        """
        if action not in cls.LIMITS:
            raise KeyError(f"Лимит для действия '{action}' не найден")
        return cls.LIMITS[action]
    
    @classmethod
    def get_error_message(cls, action: str, retry_after_seconds: int) -> str:
        """
        Получить сообщение об ошибке при превышении лимита
        
        Args:
            action: Название действия
            retry_after_seconds: Через сколько секунд можно повторить
            
        Returns:
            str: Сообщение об ошибке
        """
        limit = cls.get_limit(action)
        
        # Форматируем время ожидания
        if retry_after_seconds < 60:
            time_str = f"{retry_after_seconds} секунд"
        elif retry_after_seconds < 3600:
            minutes = retry_after_seconds // 60
            time_str = f"{minutes} минут"
        else:
            hours = retry_after_seconds // 3600
            time_str = f"{hours} часов"
        
        # Форматируем лимит
        if action == cls.CREATE_APPOINTMENT:
            return (
                f"⏳ **Превышен лимит создания записей**\n\n"
                f"Вы можете создавать не более **{limit.max_requests} записей в час**.\n"
                f"Попробуйте снова через **{time_str}**.\n\n"
                f"💡 Это ограничение помогает предотвратить спам и злоупотребления."
            )
        elif action == cls.CANCEL_APPOINTMENT:
            return (
                f"⏳ **Превышен лимит отмен**\n\n"
                f"Вы можете отменять не более **{limit.max_requests} записей в час**.\n"
                f"Попробуйте снова через **{time_str}**.\n\n"
                f"💡 Частые отмены могут повлиять на доступность мастеров."
            )
        else:
            return (
                f"⏳ Превышен лимит запросов.\n"
                f"Попробуйте снова через {time_str}."
            )
