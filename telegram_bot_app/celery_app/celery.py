from celery import Celery
from celery.schedules import crontab
from telegram_bot_app.core.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    "beauty_salon_bot",
    broker=f"redis://localhost:6379/1",  # используем DB 1 для Celery
    backend=f"redis://localhost:6379/1",
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
    # 🧪 ТЕСТ: Проверка напоминаний за 2 минуты (каждую минуту)
    "send-reminders-2-minutes-TEST": {
        "task": "telegram_bot_app.celery_app.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*"),  # каждую минуту
        "kwargs": {"minutes_before": 2},
    },
    # Проверка напоминаний за 1 день
    "send-reminders-1-day": {
        "task": "telegram_bot_app.celery_app.tasks.send_appointment_reminders",
        "schedule": crontab(hour=10, minute=0),  # каждый день в 10:00
        "kwargs": {"hours_before": 24},
    },
    # Проверка напоминаний за 1 час
    "send-reminders-1-hour": {
        "task": "telegram_bot_app.celery_app.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*/30"),  # каждые 30 минут
        "kwargs": {"hours_before": 1},
    },
}