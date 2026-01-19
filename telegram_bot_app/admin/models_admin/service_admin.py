from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.service import Service


class ServiceAdmin(ModelView, model=Service):
    column_list = [
        "name",
        "salon",
        "duration_minutes",
        "price",
        "is_active"
    ]

    column_labels = {
        "name": "Название услуги",
        "salon": "Салон",
        "duration_minutes": "Длительность (мин)",
        "price": "Цена",
        "is_active": "Активна"
    }

    column_searchable_list = [
        "name"
    ]

    column_sortable_list = [
        "name",
        "duration_minutes",
        "price",
        "is_active"
    ]

    form_columns = [
        "name",
        "salon",
        "duration_minutes",
        "price",
        "is_active"
    ]

    column_default_sort = [("name", True)]

    def get_query(self):
        return super().get_query().options(
            selectinload(Service.salon),
            selectinload(Service.master_services),
            selectinload(Service.appointments)
        )

    def get_count_query(self):
        return super().get_count_query()