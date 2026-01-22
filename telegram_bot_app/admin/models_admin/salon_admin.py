from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from sqlalchemy import event
from telegram_bot_app.models.salon import Salon
from telegram_bot_app.services.gis_service import update_gis_link


class SalonAdmin(ModelView, model=Salon):
    """Админ-панель для управления салонами с автоматическим обновлением GIS ссылок."""
    
    identity = "salon"
    name = "Салоны"
    name_plural = "Салоны"
    
    column_list = ["name", "address", "description", "gis_link", "is_active"]
    
    column_labels = {
        "name": "Название",
        "address": "Адрес", 
        "description": "Описание",
        "gis_link": "Ссылка 2GIS",
        "is_active": "Активен"
    }
    
    column_searchable_list = ["name", "address", "description"]
    column_sortable_list = ["name", "is_active"]
    
    form_columns = ["name", "address", "description", "gis_link", "is_active"]
    
    form_widget_args = {
        "gis_link": {"readonly": True}
    }
    
    column_default_sort = [("name", True)]

    def get_query(self):
        """Возвращает запрос с предзагруженными связанными данными."""
        return super().get_query().options(
            selectinload(Salon.services),
            selectinload(Salon.masters),
            selectinload(Salon.appointments)
        )

    def get_count_query(self):
        """Возвращает запрос для подсчета общего количества записей."""
        return super().get_count_query()

    async def on_model_change(self, data, model, is_created, request):
        """
        Хук для автоматического обновления GIS ссылки при изменении модели.
        
        Args:
            data: Данные формы
            model: Объект модели
            is_created: Флаг создания новой записи
            request: HTTP запрос
        """
        await super().on_model_change(data, model, is_created, request)
        
        # Обновляем GIS ссылку только при создании или изменении адреса
        if is_created or 'address' in data:
            await self._update_gis_link_async(model.id)

    async def after_model_change(self, data, model, is_created, request):
        """
        Хук после сохранения модели для обновления отображаемых данных.
        
        Args:
            data: Данные формы
            model: Объект модели
            is_created: Флаг создания новой записи
            request: HTTP запрос
        """
        await super().after_model_change(data, model, is_created, request)
        
        # Обновляем gis_link в текущей модели для корректного отображения
        await self._refresh_model_gis_link(model)

    async def _update_gis_link_async(self, salon_id: int):
        """
        Асинхронно обновляет GIS ссылку для салона.
        
        Args:
            salon_id: ID салона для обновления
        """
        try:
            from telegram_bot_app.db.base import async_session
            from telegram_bot_app.crud.salon import SalonCRUD
            
            async with async_session() as db:
                salon_crud = SalonCRUD(db)
                salon = await salon_crud.get(salon_id)
                
                if salon and salon.address:
                    await update_gis_link(salon, db)
                    
        except Exception:
            # Ошибки логируются в GIS сервисе, прерывать процесс сохранения не нужно
            pass

    async def _refresh_model_gis_link(self, model):
        """
        Обновляет gis_link в модели из базы данных.
        
        Args:
            model: Модель для обновления
        """
        try:
            from telegram_bot_app.db.base import async_session
            from telegram_bot_app.crud.salon import SalonCRUD
            
            async with async_session() as db:
                salon_crud = SalonCRUD(db)
                fresh_model = await salon_crud.get(model.id)
                
                if fresh_model and fresh_model.gis_link:
                    model.gis_link = fresh_model.gis_link
                    
        except Exception:
            # Ошибки обновления модели не критичны
            pass


@event.listens_for(Salon, 'after_insert')
@event.listens_for(Salon, 'after_update')
def on_salon_change(mapper, connection, target):
    """
    SQLAlchemy event listener для автоматического обновления GIS ссылок.
    Вызывается после вставки или обновления записи салона.
    
    Args:
        mapper: SQLAlchemy маппер
        connection: Соединение с базой данных
        target: Объект салона
    """
    if hasattr(target, 'address') and target.address:
        import asyncio
        from telegram_bot_app.db.base import async_session
        
        async def update_gis_async():
            async with async_session() as db:
                from telegram_bot_app.crud.salon import SalonCRUD
                salon_crud = SalonCRUD(db)
                fresh_salon = await salon_crud.get(target.id)
                
                if fresh_salon:
                    await update_gis_link(fresh_salon, db)
        
        # Запускаем асинхронное обновление
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(update_gis_async())
            else:
                asyncio.run(update_gis_async())
        except Exception:
            # Ошибки логируются в GIS сервисе
            pass