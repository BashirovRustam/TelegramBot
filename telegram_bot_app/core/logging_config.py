"""
Настройка логирования для Telegram бота
Файл: telegram_bot_app/core/logging_config.py

Правила:
🟢 INFO и WARNING → только консоль
🔴 ERROR и CRITICAL → файл + консоль
"""

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logging(log_level: str = "INFO"):
    """
    Настройка логирования для всего приложения

    Args:
        log_level: уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    # Создаем папку для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Получаем root logger (главный логгер для всего приложения)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # принимаем все уровни

    # Очищаем старые handlers если они есть
    root_logger.handlers.clear()

    # ============================================
    # HANDLER 1: Консоль (все уровни)
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # показываем INFO и выше

    # Формат для консоли (короткий)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # ============================================
    # HANDLER 2: Файл error.log (только ERROR и CRITICAL)
    # ============================================
    error_file_handler = TimedRotatingFileHandler(
        filename=log_dir / "error.log",
        when='midnight',  # новый файл каждую полночь
        interval=1,
        backupCount=30,  # храним 30 дней
        encoding='utf-8'
    )
    error_file_handler.suffix = "%Y-%m-%d"
    error_file_handler.setLevel(logging.ERROR)  # только ERROR и CRITICAL

    # Формат для файла (подробный)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_file_handler.setFormatter(file_formatter)

    # ============================================
    # Добавляем handlers к root logger
    # ============================================
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_file_handler)

    # ============================================
    # Отключаем лишние логи от библиотек
    # ============================================
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('redis').setLevel(logging.WARNING)

    # Логируем успешную настройку
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("🚀 Логирование настроено")
    logger.info(f"   Уровень: {log_level}")
    logger.info(f"   🟢 INFO/WARNING → консоль")
    logger.info(f"   🔴 ERROR/CRITICAL → logs/error.log + консоль")
    logger.info("=" * 70)