from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.crud.salon import SalonCRUD


class SalonService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.salon_crud = SalonCRUD(db)

    async def get_active_salon_names(self) -> List[str]:
        """
        Возвращает список активных салонов для FSM.
        
        Returns:
            List[str]: Список названий активных салонов
        """
        active_salons = await self.salon_crud.get_active()
        return [salon.name for salon in active_salons]