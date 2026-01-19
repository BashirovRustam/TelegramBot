from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.master_service import MasterService


class MasterServiceAdmin(ModelView, model=MasterService):
    column_list = [
        "master",
        "service"
    ]

    column_labels = {
        "master": "Мастер",
        "service": "Услуга"
    }

    column_searchable_list = [
        "master.user.full_name",
        "service.name"
    ]

    column_sortable_list = [
        "master",
        "service"
    ]

    form_columns = [
        "master",
        "service"
    ]

    column_default_sort = [("service", True)]

    def get_query(self):
        return super().get_query().options(
            selectinload(MasterService.master).selectinload("user"),
            selectinload(MasterService.service)
        )

    def get_count_query(self):
        return super().get_count_query()