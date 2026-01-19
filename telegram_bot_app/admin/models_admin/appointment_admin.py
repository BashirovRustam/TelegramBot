from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.appointment import Appointment


class AppointmentAdmin(ModelView, model=Appointment):
    column_list = [
        "client",
        "salon",
        "master",
        "service",
        "date",
        "time_start",
        "time_end",
        "status"
    ]

    column_labels = {
        "client": "Клиент",
        "salon": "Салон",
        "master": "Мастер",
        "service": "Услуга",
        "date": "Дата",
        "time_start": "Время начала",
        "time_end": "Время окончания",
        "status": "Статус"
    }

    column_searchable_list = []

    column_sortable_list = [
        "date",
        "time_start",
        "status"
    ]

    form_columns = [
        "client_id",
        "salon_id",
        "master_id",
        "service_id",
        "date",
        "time_start",
        "time_end",
        "status"
    ]

    column_default_sort = [("date", False), ("time_start", False)]

    # Используем selectinload для ВСЕХ связей включая вложенные
    def get_query(self):
        return super().get_query().options(
            selectinload(Appointment.client),
            selectinload(Appointment.salon),
            selectinload(Appointment.master).selectinload(Master.user),
            selectinload(Appointment.master).selectinload(Master.salon),
            selectinload(Appointment.service).selectinload(Service.salon)
        )

    def get_count_query(self):
        return super().get_count_query()

    # Formatters с безопасной обработкой
    column_formatters = {
        "client": lambda m, a: getattr(m.client, 'full_name', 'БЕЗ ИМЕНИ') if m and m.client else "БЕЗ ИМЕНИ",
        "master": lambda m, a: getattr(m.master.user, 'full_name', f"Мастер #{m.master_id}") if (
                    m and m.master and hasattr(m.master, 'user') and m.master.user) else (
            f"Мастер #{m.master_id}" if m else ""),
        "salon": lambda m, a: getattr(m.salon, 'name', f"Салон #{m.salon_id}") if m and m.salon else (
            f"Салон #{m.salon_id}" if m else ""),
        "service": lambda m, a: getattr(m.service, 'name', f"Услуга #{m.service_id}") if m and m.service else (
            f"Услуга #{m.service_id}" if m else "")
    }

    column_formatters_detail = {
        "client": lambda m, a: getattr(m.client, 'full_name', 'БЕЗ ИМЕНИ') if m and m.client else "БЕЗ ИМЕНИ",
        "master": lambda m, a: getattr(m.master.user, 'full_name', f"Мастер #{m.master_id}") if (
                    m and m.master and hasattr(m.master, 'user') and m.master.user) else (
            f"Мастер #{m.master_id}" if m else ""),
        "salon": lambda m, a: getattr(m.salon, 'name', f"Салон #{m.salon_id}") if m and m.salon else (
            f"Салон #{m.salon_id}" if m else ""),
        "service": lambda m, a: getattr(m.service, 'name', f"Услуга #{m.service_id}") if m and m.service else (
            f"Услуга #{m.service_id}" if m else "")
    }


# Добавляем импорты в начало файла
from telegram_bot_app.models.master import Master
from telegram_bot_app.models.service import Service