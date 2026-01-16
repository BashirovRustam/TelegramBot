from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.service import Service
from telegram_bot_app.schemas.service import ServiceCreate, ServiceUpdate


class ServiceCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, service_id: int) -> Optional[Service]:
        """Получить услугу по ID"""
        result = await self.db.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Получить все услуги с пагинацией"""
        result = await self.db.execute(
            select(Service).offset(skip).limit(limit).order_by(Service.id)
        )
        return result.scalars().all()

    async def get_by_salon_id(self, salon_id: int, skip: int = 0, limit: int = 100) -> List[Service]:
        """Получить услуги салона"""
        result = await self.db.execute(
            select(Service)
            .where(Service.salon_id == salon_id)
            .offset(skip)
            .limit(limit)
            .order_by(Service.name)
        )
        return result.scalars().all()

    async def get_active_by_salon_id(self, salon_id: int, skip: int = 0, limit: int = 100) -> List[Service]:
        """Получить активные услуги салона"""
        result = await self.db.execute(
            select(Service)
            .where(and_(Service.salon_id == salon_id, Service.is_active == True))
            .offset(skip)
            .limit(limit)
            .order_by(Service.name)
        )
        return result.scalars().all()

    async def get_by_name(self, name: str, salon_id: Optional[int] = None) -> Optional[Service]:
        """Получить услугу по названию (опционально для конкретного салона)"""
        query = select(Service).where(Service.name == name)
        if salon_id:
            query = query.where(Service.salon_id == salon_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Поиск услуг по названию"""
        result = await self.db.execute(
            select(Service)
            .where(Service.name.ilike(f"%{name_query}%"))
            .offset(skip)
            .limit(limit)
            .order_by(Service.name)
        )
        return result.scalars().all()

    async def get_by_price_range(self, min_price: float, max_price: float, skip: int = 0, limit: int = 100) -> List[Service]:
        """Получить услуги в ценовом диапазоне"""
        result = await self.db.execute(
            select(Service)
            .where(and_(Service.price >= min_price, Service.price <= max_price))
            .offset(skip)
            .limit(limit)
            .order_by(Service.price)
        )
        return result.scalars().all()

    async def create(self, service_create: ServiceCreate) -> Service:
        """Создать новую услугу"""
        db_service = Service(**service_create.model_dump())
        self.db.add(db_service)
        await self.db.commit()
        await self.db.refresh(db_service)
        return db_service

    async def update(self, service_id: int, service_update: ServiceUpdate) -> Optional[Service]:
        """Обновить данные услуги"""
        db_service = await self.get(service_id)
        if not db_service:
            return None
        
        update_data = service_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_service, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_service)
        return db_service

    async def delete(self, service_id: int) -> bool:
        """Удалить услугу"""
        db_service = await self.get(service_id)
        if not db_service:
            return False
        
        await self.db.delete(db_service)
        await self.db.commit()
        return True

    async def get_with_relations(self, service_id: int) -> Optional[Service]:
        """Получить услугу со связанными данными"""
        result = await self.db.execute(
            select(Service)
            .options(
                selectinload(Service.salon),
                selectinload(Service.master_services),
                selectinload(Service.appointments)
            )
            .where(Service.id == service_id)
        )
        return result.scalar_one_or_none()


# Dependency function
def get_service_crud(db: AsyncSession) -> ServiceCRUD:
    return ServiceCRUD(db)
