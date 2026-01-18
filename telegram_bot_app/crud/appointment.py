from datetime import date, time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.appointment import Appointment, AppointmentStatusEnum
from telegram_bot_app.models.user import User
from telegram_bot_app.models.master import Master
from telegram_bot_app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class AppointmentCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, appointment_id: int) -> Optional[Appointment]:
        """Получить запись по ID"""
        result = await self.db.execute(select(Appointment).where(Appointment.id == appointment_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить все записи с пагинацией"""
        result = await self.db.execute(
            select(Appointment).offset(skip).limit(limit).order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def get_by_client_id(self, client_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить записи клиента"""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.client_id == client_id)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def get_by_master_id(self, master_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить записи мастера"""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.master_id == master_id)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def get_by_salon_id(self, salon_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить записи салона"""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.salon_id == salon_id)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def get_by_date(self, appointment_date: date, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить записи на конкретную дату"""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.date == appointment_date)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.time_start)
        )
        return result.scalars().all()

    async def get_by_master_and_date(self, master_id: int, appointment_date: date) -> List[Appointment]:
        """Получить записи мастера на конкретную дату"""
        result = await self.db.execute(
            select(Appointment)
            .where(and_(Appointment.master_id == master_id, Appointment.date == appointment_date))
            .order_by(Appointment.time_start)
        )
        return result.scalars().all()

    async def get_by_status(self, status: AppointmentStatusEnum, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить записи по статусу"""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def get_active_by_client(self, client_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Получить активные записи клиента"""
        result = await self.db.execute(
            select(Appointment)
            .where(and_(Appointment.client_id == client_id, Appointment.status == AppointmentStatusEnum.BOOKED))
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.date.desc(), Appointment.time_start.desc())
        )
        return result.scalars().all()

    async def check_time_conflict(
        self, 
        master_id: int, 
        appointment_date: date, 
        time_start: time, 
        time_end: time,
        exclude_appointment_id: Optional[int] = None
    ) -> bool:
        """Проверить конфликт времени записи"""
        print(f"DEBUG CRUD: Checking conflict - master_id={master_id}, date={appointment_date}, start={time_start}, end={time_end}")
        
        query = select(Appointment).where(
            and_(
                Appointment.master_id == master_id,
                Appointment.date == appointment_date,
                Appointment.status == AppointmentStatusEnum.BOOKED,
                or_(
                    and_(Appointment.time_start <= time_start, Appointment.time_end > time_start),
                    and_(Appointment.time_start < time_end, Appointment.time_end >= time_end),
                    and_(Appointment.time_start >= time_start, Appointment.time_end <= time_end)
                )
            )
        )
        
        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)
        
        print(f"DEBUG CRUD: SQL query = {query}")
        
        result = await self.db.execute(query)
        conflict_appointment = result.scalar_one_or_none()
        
        print(f"DEBUG CRUD: Conflict appointment = {conflict_appointment}")
        print(f"DEBUG CRUD: Has conflict = {conflict_appointment is not None}")
        
        return conflict_appointment is not None

    async def create(self, appointment_create: AppointmentCreate) -> Appointment:
        """Создать новую запись"""
        db_appointment = Appointment(**appointment_create.model_dump())
        self.db.add(db_appointment)
        await self.db.commit()
        await self.db.refresh(db_appointment)
        return db_appointment

    async def update(self, appointment_id: int, appointment_update: AppointmentUpdate) -> Optional[Appointment]:
        """Обновить запись"""
        db_appointment = await self.get(appointment_id)
        if not db_appointment:
            return None
        
        update_data = appointment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_appointment, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_appointment)
        return db_appointment

    async def cancel(self, appointment_id: int) -> Optional[Appointment]:
        """Отменить запись"""
        return await self.update(appointment_id, AppointmentUpdate(status=AppointmentStatusEnum.CANCELLED))

    async def complete(self, appointment_id: int) -> Optional[Appointment]:
        """Завершить запись"""
        return await self.update(appointment_id, AppointmentUpdate(status=AppointmentStatusEnum.COMPLETED))

    async def delete(self, appointment_id: int) -> bool:
        """Удалить запись"""
        db_appointment = await self.get(appointment_id)
        if not db_appointment:
            return False
        
        await self.db.delete(db_appointment)
        await self.db.commit()
        return True

    async def get_with_relations(self, appointment_id: int) -> Optional[Appointment]:
        """Получить запись со связанными данными"""
        result = await self.db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.client),
                selectinload(Appointment.salon),
                selectinload(Appointment.master).selectinload(Master.user),
                selectinload(Appointment.service)
            )
            .where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_upcoming_appointments(self, master_id: int, current_date: date, current_time: time) -> List[Appointment]:
        """Получить предстоящие записи мастера"""
        result = await self.db.execute(
            select(Appointment)
            .where(
                and_(
                    Appointment.master_id == master_id,
                    Appointment.date >= current_date,
                    Appointment.status == AppointmentStatusEnum.BOOKED,
                    or_(
                        Appointment.date > current_date,
                        and_(Appointment.date == current_date, Appointment.time_start > current_time)
                    )
                )
            )
            .order_by(Appointment.date, Appointment.time_start)
        )
        return result.scalars().all()


# Dependency function
def get_appointment_crud(db: AsyncSession) -> AppointmentCRUD:
    return AppointmentCRUD(db)
