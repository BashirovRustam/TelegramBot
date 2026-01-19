from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.master import Master


class MasterAdmin(ModelView, model=Master):
    column_list = [
        "user",
        "salon",
        "is_active"
    ]

    column_labels = {
        "user": "Мастер",
        "salon": "Салон",
        "is_active": "Активен"
    }

    column_searchable_list = []

    column_sortable_list = [
        "is_active"
    ]

    form_columns = [
        "user",
        "salon",
        "is_active"
    ]

    column_default_sort = [("id", False)]

    def get_query(self):
        return super().get_query().options(
            selectinload(Master.user),
            selectinload(Master.salon),
            selectinload(Master.master_services).selectinload("service"),
            selectinload(Master.schedules),
            selectinload(Master.appointments)
        )

    def get_count_query(self):
        return super().get_count_query()