from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from telegram_bot_app.crud.salon import SalonCRUD
from telegram_bot_app.crud.service import ServiceCRUD
from telegram_bot_app.crud.master import MasterCRUD
from telegram_bot_app.models.master import Master


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