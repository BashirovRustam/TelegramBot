from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.master import Master
from app.schemas.master import MasterCreate, MasterUpdate


class MasterCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, master_id: int) -> Optional[Master]:
        """Получить мастера по ID"""
        result = await self.db.execute(select(Master).where(Master.id == master_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Master]:
        """Получить всех мастеров с пагинацией"""
        result = await self.db.execute(
            select(Master).offset(skip).limit(limit).order_by(Master.id)
        )
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> Optional[Master]:
        """Получить мастера по ID пользователя"""
        result = await self.db.execute(select(Master).where(Master.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_salon_id(self, salon_id: int, skip: int = 0, limit: int = 100) -> List[Master]:
        """Получить мастеров салона"""
        result = await self.db.execute(
            select(Master)
            .where(Master.salon_id == salon_id)
            .offset(skip)
            .limit(limit)
            .order_by(Master.id)
        )
        return result.scalars().all()

    async def get_active_by_salon_id(self, salon_id: int, skip: int = 0, limit: int = 100) -> List[Master]:
        """Получить активных мастеров салона"""
        result = await self.db.execute(
            select(Master)
            .where(and_(Master.salon_id == salon_id, Master.is_active == True))
            .offset(skip)
            .limit(limit)
            .order_by(Master.id)
        )
        return result.scalars().all()

    async def get_active_masters(self, skip: int = 0, limit: int = 100) -> List[Master]:
        """Получить всех активных мастеров"""
        result = await self.db.execute(
            select(Master)
            .where(Master.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Master.id)
        )
        return result.scalars().all()

    async def create(self, master_create: MasterCreate) -> Master:
        """Создать нового мастера"""
        db_master = Master(**master_create.model_dump())
        self.db.add(db_master)
        await self.db.commit()
        await self.db.refresh(db_master)
        return db_master

    async def update(self, master_id: int, master_update: MasterUpdate) -> Optional[Master]:
        """Обновить данные мастера"""
        db_master = await self.get(master_id)
        if not db_master:
            return None
        
        update_data = master_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_master, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_master)
        return db_master

    async def delete(self, master_id: int) -> bool:
        """Удалить мастера"""
        db_master = await self.get(master_id)
        if not db_master:
            return False
        
        await self.db.delete(db_master)
        await self.db.commit()
        return True

    async def get_with_relations(self, master_id: int) -> Optional[Master]:
        """Получить мастера со связанными данными"""
        result = await self.db.execute(
            select(Master)
            .options(
                selectinload(Master.user),
                selectinload(Master.salon),
                selectinload(Master.master_services),
                selectinload(Master.schedules),
                selectinload(Master.appointments)
            )
            .where(Master.id == master_id)
        )
        return result.scalar_one_or_none()


# Dependency function
def get_master_crud(db: AsyncSession) -> MasterCRUD:
    return MasterCRUD(db)
