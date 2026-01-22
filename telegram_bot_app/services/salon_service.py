from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from telegram_bot_app.crud.salon import SalonCRUD
from telegram_bot_app.crud.service import ServiceCRUD
from telegram_bot_app.crud.master import MasterCRUD
from telegram_bot_app.models.master import Master
from telegram_bot_app.models.salon import Salon
from telegram_bot_app.services.gis_service import update_gis_link


class SalonService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.salon_crud = SalonCRUD(db)
        self.service_crud = ServiceCRUD(db)
        self.master_crud = MasterCRUD(db)

    async def get_by_id(self, salon_id: int):
        """
        Возвращает объект салона по ID или None.
        Абстрагируем CRUD от handler.
        """
        return await self.salon_crud.get(salon_id)

    async def get_services_by_salon(self, salon_id: int) -> List:
        """
        Возвращает список активных услуг салона.
        
        Args:
            salon_id: ID салона
            
        Returns:
            List[Service]: Список активных услуг салона
        """
        return await self.service_crud.get_active_by_salon_id(salon_id)

    async def get_master_by_salon(self, salon_id: int) -> List[Master]:
        """
        Возвращает список активных мастеров салона.
        
        Args:
            salon_id: ID салона
            
        Returns:
            List[Master]: Список активных мастеров салона
        """
        return await self.master_crud.get_active_by_salon_id_with_user(salon_id)
    
    async def create_salon(self, salon_data: dict) -> Salon:
        """
        Создает новый салон и автоматически обновляет GIS ссылку
        
        Args:
            salon_data: Данные для создания салона
            
        Returns:
            Salon: Созданный салон с обновленной GIS ссылкой
        """
        salon = await self.salon_crud.create(salon_data)
        
        # Обновляем GIS ссылку
        await update_gis_link(salon, self.db)
        
        return salon
    
    async def update_salon(self, salon_id: int, salon_data: dict) -> Optional[Salon]:
        """
        Обновляет салон и автоматически обновляет GIS ссылку если адрес изменился
        
        Args:
            salon_id: ID салона
            salon_data: Данные для обновления
            
        Returns:
            Optional[Salon]: Обновленный салон или None если не найден
        """
        salon = await self.salon_crud.update(salon_id, salon_data)
        
        if salon and 'address' in salon_data:
            # Если адрес изменился, обновляем GIS ссылку
            await update_gis_link(salon, self.db)
        
        return salon