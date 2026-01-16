from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.master_service import MasterService
from telegram_bot_app.schemas.master_service import MasterServiceCreate, MasterServiceUpdate


class MasterServiceCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, master_id: int, service_id: int) -> Optional[MasterService]:
        """Получить связь мастера с услугой"""
        result = await self.db.execute(
            select(MasterService)
            .where(and_(MasterService.master_id == master_id, MasterService.service_id == service_id))
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MasterService]:
        """Получить все связи мастеров с услугами"""
        result = await self.db.execute(
            select(MasterService).offset(skip).limit(limit).order_by(MasterService.master_id, MasterService.service_id)
        )
        return result.scalars().all()

    async def get_by_master_id(self, master_id: int) -> List[MasterService]:
        """Получить все услуги мастера"""
        result = await self.db.execute(
            select(MasterService)
            .where(MasterService.master_id == master_id)
            .order_by(MasterService.service_id)
        )
        return result.scalars().all()

    async def get_by_service_id(self, service_id: int) -> List[MasterService]:
        """Получить всех мастеров для услуги"""
        result = await self.db.execute(
            select(MasterService)
            .where(MasterService.service_id == service_id)
            .order_by(MasterService.master_id)
        )
        return result.scalars().all()

    async def get_master_service_ids(self, master_id: int) -> List[int]:
        """Получить ID всех услуг мастера"""
        result = await self.db.execute(
            select(MasterService.service_id)
            .where(MasterService.master_id == master_id)
            .order_by(MasterService.service_id)
        )
        return [row[0] for row in result.all()]

    async def get_service_master_ids(self, service_id: int) -> List[int]:
        """Получить ID всех мастеров для услуги"""
        result = await self.db.execute(
            select(MasterService.master_id)
            .where(MasterService.service_id == service_id)
            .order_by(MasterService.master_id)
        )
        return [row[0] for row in result.all()]

    async def create(self, master_service_create: MasterServiceCreate) -> MasterService:
        """Создать связь мастера с услугой"""
        db_master_service = MasterService(**master_service_create.model_dump())
        self.db.add(db_master_service)
        await self.db.commit()
        await self.db.refresh(db_master_service)
        return db_master_service

    async def create_multiple(self, master_id: int, service_ids: List[int]) -> List[MasterService]:
        """Создать несколько связей мастера с услугами"""
        master_services = []
        for service_id in service_ids:
            master_service = MasterService(master_id=master_id, service_id=service_id)
            self.db.add(master_service)
            master_services.append(master_service)
        
        await self.db.commit()
        for master_service in master_services:
            await self.db.refresh(master_service)
        
        return master_services

    async def update(self, master_id: int, service_id: int, master_service_update: MasterServiceUpdate) -> Optional[MasterService]:
        """Обновить связь мастера с услугой (только для замены)"""
        # Сначала удаляем старую связь
        await self.delete(master_id, service_id)
        
        # Создаем новую связь
        new_master_service = MasterService(
            master_id=master_service_update.master_id,
            service_id=master_service_update.service_id
        )
        self.db.add(new_master_service)
        await self.db.commit()
        await self.db.refresh(new_master_service)
        return new_master_service

    async def delete(self, master_id: int, service_id: int) -> bool:
        """Удалить связь мастера с услугой"""
        result = await self.db.execute(
            delete(MasterService)
            .where(and_(MasterService.master_id == master_id, MasterService.service_id == service_id))
        )
        await self.db.commit()
        return result.rowcount > 0

    async def delete_by_master_id(self, master_id: int) -> bool:
        """Удалить все связи мастера"""
        result = await self.db.execute(
            delete(MasterService).where(MasterService.master_id == master_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def delete_by_service_id(self, service_id: int) -> bool:
        """Удалить все связи услуги"""
        result = await self.db.execute(
            delete(MasterService).where(MasterService.service_id == service_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_with_relations(self, master_id: int, service_id: int) -> Optional[MasterService]:
        """Получить связь со связанными данными"""
        result = await self.db.execute(
            select(MasterService)
            .options(
                selectinload(MasterService.master),
                selectinload(MasterService.service)
            )
            .where(and_(MasterService.master_id == master_id, MasterService.service_id == service_id))
        )
        return result.scalar_one_or_none()


# Dependency function
def get_master_service_crud(db: AsyncSession) -> MasterServiceCRUD:
    return MasterServiceCRUD(db)
