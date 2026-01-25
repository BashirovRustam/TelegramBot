from celery import Celery
from celery.schedules import crontab
from telegram_bot_app.core.config import settings
import os

# Создаем экземпляр Celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
celery_app = Celery(
    "beauty_salon_bot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["telegram_bot_app.celery_app.tasks"]
)

# Конфигурация
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",  # твой часовой пояс
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут максимум на задачу
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Периодические задачи (beat schedule)
celery_app.conf.beat_schedule = {
    # ⏰ Проверка напоминаний за 60 минут (каждую минуту для точности)
    "send-reminders-60-minutes": {
        "task": "telegram_bot_app.celery_app.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*"),  # каждую минуту
        "kwargs": {"minutes_before": 60},  # за 60 минут = 1 час
    },
    # 📅 Проверка напоминаний за 1 день (раз в день в 10:00)
    "send-reminders-1-day": {
        "task": "telegram_bot_app.celery_app.tasks.send_appointment_reminders",
        "schedule": crontab(hour=10, minute=0),  # каждый день в 10:00
        "kwargs": {"hours_before": 24},
    },
}