from typing import List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from telegram_bot_app.crud.salon import SalonCRUD
from telegram_bot_app.crud.service import ServiceCRUD
from telegram_bot_app.crud.master import MasterCRUD
from telegram_bot_app.models.master import Master

logger = logging.getLogger(__name__)


class SalonService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.salon_crud = SalonCRUD(db)
        self.service_crud = ServiceCRUD(db)
        self.master_crud = MasterCRUD(db)

    async def get_by_id(self, salon_id: int):
        """Возвращает объект салона по ID или None."""
        logger.debug("Получение салона по ID: salon_id=%d", salon_id)

        try:
            salon = await self.salon_crud.get(salon_id)

            if salon:
                logger.debug("Салон найден: salon_id=%d, name=%s", salon_id, salon.name)
            else:
                logger.warning("Салон не найден: salon_id=%d", salon_id)

            return salon

        except Exception as e:
            logger.error(
                "Ошибка получения салона salon_id=%d: %s",
                salon_id, e, exc_info=True
            )
            return None

    async def get_services_by_salon(self, salon_id: int) -> List:
        """Возвращает список активных услуг салона."""
        logger.info("Получение услуг для салона: salon_id=%d", salon_id)

        try:
            services = await self.service_crud.get_active_by_salon_id(salon_id)

            logger.info(
                "Найдено услуг: %d для salon_id=%d",
                len(services), salon_id
            )

            return services

        except Exception as e:
            logger.error(
                "Ошибка получения услуг для salon_id=%d: %s",
                salon_id, e, exc_info=True
            )
            return []

    async def get_master_by_salon(self, salon_id: int) -> List[Master]:
        """Возвращает список активных мастеров салона."""
        logger.info("Получение мастеров для салона: salon_id=%d", salon_id)

        try:
            masters = await self.master_crud.get_active_by_salon_id_with_user(salon_id)

            logger.info(
                "Найдено мастеров: %d для salon_id=%d",
                len(masters), salon_id
            )

            return masters

        except Exception as e:
            logger.error(
                "Ошибка получения мастеров для salon_id=%d: %s",
                salon_id, e, exc_info=True
            )
            return []