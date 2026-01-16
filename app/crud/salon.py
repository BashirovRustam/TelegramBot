from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.salon import Salon
from app.schemas.salon import SalonCreate, SalonUpdate


class SalonCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, salon_id: int) -> Optional[Salon]:
        """Получить салон по ID"""
        result = await self.db.execute(select(Salon).where(Salon.id == salon_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Salon]:
        """Получить все салоны с пагинацией"""
        result = await self.db.execute(
            select(Salon).offset(skip).limit(limit).order_by(Salon.id)
        )
        return result.scalars().all()

    async def get_active(self, skip: int = 0, limit: int = 100) -> List[Salon]:
        """Получить активные салоны"""
        result = await self.db.execute(
            select(Salon)
            .where(Salon.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Salon.id)
        )
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Salon]:
        """Получить салон по названию"""
        result = await self.db.execute(select(Salon).where(Salon.name == name))
        return result.scalar_one_or_none()

    async def search_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> List[Salon]:
        """Поиск салонов по названию"""
        result = await self.db.execute(
            select(Salon)
            .where(Salon.name.ilike(f"%{name_query}%"))
            .offset(skip)
            .limit(limit)
            .order_by(Salon.name)
        )
        return result.scalars().all()

    async def create(self, salon_create: SalonCreate) -> Salon:
        """Создать новый салон"""
        db_salon = Salon(**salon_create.model_dump())
        self.db.add(db_salon)
        await self.db.commit()
        await self.db.refresh(db_salon)
        return db_salon

    async def update(self, salon_id: int, salon_update: SalonUpdate) -> Optional[Salon]:
        """Обновить данные салона"""
        db_salon = await self.get(salon_id)
        if not db_salon:
            return None
        
        update_data = salon_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_salon, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_salon)
        return db_salon

    async def delete(self, salon_id: int) -> bool:
        """Удалить салон"""
        db_salon = await self.get(salon_id)
        if not db_salon:
            return False
        
        await self.db.delete(db_salon)
        await self.db.commit()
        return True

    async def get_with_relations(self, salon_id: int) -> Optional[Salon]:
        """Получить салон со связанными данными"""
        result = await self.db.execute(
            select(Salon)
            .options(
                selectinload(Salon.services),
                selectinload(Salon.masters),
                selectinload(Salon.appointments)
            )
            .where(Salon.id == salon_id)
        )
        return result.scalar_one_or_none()


# Dependency function
def get_salon_crud(db: AsyncSession) -> SalonCRUD:
    return SalonCRUD(db)
