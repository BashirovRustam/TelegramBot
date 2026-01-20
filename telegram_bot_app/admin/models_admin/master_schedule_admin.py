from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.master_schedule import MasterSchedule
from telegram_bot_app.models.master import Master


class MasterScheduleAdmin(ModelView, model=MasterSchedule):
    column_list = [
        "master_id",
        "weekday",
        "time_from",
        "time_to"
    ]

    column_labels = {
        "master_id": "Мастер",
        "weekday": "День недели",
        "time_from": "Время начала",
        "time_to": "Время окончания"
    }

    column_searchable_list = []

    column_sortable_list = [
        "master_id",
        "weekday",
        "time_from",
        "time_to"
    ]

    form_columns = [
        "master_id",
        "weekday",
        "time_from",
        "time_to"
    ]

    column_default_sort = [("weekday", True), ("time_from", True)]

    # Загружаем связи
    def get_query(self):
        return super().get_query().options(
            selectinload(MasterSchedule.master).selectinload(Master.user)
        )

    def get_count_query(self):
        return super().get_count_query()

    # Formatters для всех полей
    column_formatters = {
        "master_id": lambda m, a: m.master.user.full_name if (
                    m and m.master and m.master.user) else f"Мастер #{m.master_id}",
        "weekday": lambda m, a: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][m.weekday] if m else "",
        "time_from": lambda m, a: m.time_from.strftime("%H:%M") if (m and m.time_from) else "",
        "time_to": lambda m, a: m.time_to.strftime("%H:%M") if (m and m.time_to) else ""
    }

    column_formatters_detail = {
        "master_id": lambda m, a: m.master.user.full_name if (
                    m and m.master and m.master.user) else f"Мастер #{m.master_id}",
        "weekday": lambda m, a: ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][
            m.weekday] if m else "",
        "time_from": lambda m, a: m.time_from.strftime("%H:%M") if (m and m.time_from) else "",
        "time_to": lambda m, a: m.time_to.strftime("%H:%M") if (m and m.time_to) else ""
    }