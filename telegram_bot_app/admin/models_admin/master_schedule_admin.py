from sqladmin import ModelView
from sqlalchemy.orm import joinedload
from telegram_bot_app.models.master_schedule import MasterSchedule


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
    
    def format_master_id(view=None, context=None, model=None, name=None):
        if model is None:
            return ""
        # Показываем ID мастера, так как связь вызывает ошибку
        return f"Мастер #{model.master_id}"
    
    def format_weekday(view=None, context=None, model=None, name=None):
        if model is None:
            return ""
        return ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][model.weekday]
    
    def format_weekday_detail(view=None, context=None, model=None, name=None):
        if model is None:
            return ""
        return ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][model.weekday]
    
    def format_time_from(view=None, context=None, model=None, name=None):
        if model is None:
            return ""
        return model.time_from.strftime("%H:%M") if model.time_from else ""
    
    def format_time_to(view=None, context=None, model=None, name=None):
        if model is None:
            return ""
        return model.time_to.strftime("%H:%M") if model.time_to else ""
    
    # Временно убираем все formatters чтобы избежать ошибок
    # column_formatters_detail = {}
    # column_formatters = {}
    
    # Убираем eager loading, так как не используем связи
    def get_query(self):
        return super().get_query()
    
    def get_count_query(self):
        return super().get_count_query()
