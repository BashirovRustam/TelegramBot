from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [
        "telegram_id",
        "full_name",
        "role",
        "is_active",
        "created_at"
    ]

    column_labels = {
        "telegram_id": "Telegram ID",
        "full_name": "Полное имя",
        "role": "Роль",
        "is_active": "Активен",
        "created_at": "Дата создания"
    }

    column_searchable_list = [
        "full_name",
        "telegram_id"
    ]

    column_sortable_list = [
        "full_name",
        "role",
        "created_at"
    ]

    form_columns = [
        "telegram_id",
        "full_name",
        "role",
        "is_active"
    ]

    column_default_sort = [("created_at", False)]

    def get_query(self):
        return super().get_query().options(
            selectinload(User.master_profile)
        )

    def get_count_query(self):
        return super().get_count_query()

    column_formatters = {
        "created_at": lambda m, a: m.created_at.strftime("%d.%m.%Y") if m and m.created_at else ""
    }

    column_formatters_detail = {
        "created_at": lambda m, a: m.created_at.strftime("%d.%m.%Y %H:%M") if m and m.created_at else ""
    }
