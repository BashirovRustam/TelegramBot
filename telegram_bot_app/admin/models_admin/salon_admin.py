from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.salon import Salon


class SalonAdmin(ModelView, model=Salon):
    column_list = [
        "name",
        "address",
        "description",
        "is_active"
    ]

    column_labels = {
        "name": "Название",
        "address": "Адрес",
        "description": "Описание",
        "is_active": "Активен"
    }

    column_searchable_list = [
        "name",
        "address"
    ]

    column_sortable_list = [
        "name",
        "is_active"
    ]

    form_columns = [
        "name",
        "address",
        "description",
        "is_active"
    ]

    column_default_sort = [("name", True)]

    def get_query(self):
        return super().get_query().options(
            selectinload(Salon.services),
            selectinload(Salon.masters),
            selectinload(Salon.appointments)
        )

    def get_count_query(self):
        return super().get_count_query()