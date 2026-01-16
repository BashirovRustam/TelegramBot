from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.master_schedule import MasterSchedule
from telegram_bot_app.schemas.master_schedule import MasterScheduleCreate, MasterScheduleUpdate


class MasterScheduleCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, schedule_id: int) -> Optional[MasterSchedule]:
        """Получить расписание по ID"""
        result = await self.db.execute(select(MasterSchedule).where(MasterSchedule.id == schedule_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MasterSchedule]:
        """Получить все расписания с пагинацией"""
        result = await self.db.execute(
            select(MasterSchedule).offset(skip).limit(limit).order_by(MasterSchedule.master_id, MasterSchedule.weekday)
        )
        return result.scalars().all()

    async def get_by_master_id(self, master_id: int) -> List[MasterSchedule]:
        """Получить расписание мастера"""
        result = await self.db.execute(
            select(MasterSchedule)
            .where(MasterSchedule.master_id == master_id)
            .order_by(MasterSchedule.weekday, MasterSchedule.time_from)
        )
        return result.scalars().all()

    async def get_by_master_and_weekday(self, master_id: int, weekday: int) -> List[MasterSchedule]:
        """Получить расписание мастера на конкретный день недели"""
        result = await self.db.execute(
            select(MasterSchedule)
            .where(and_(MasterSchedule.master_id == master_id, MasterSchedule.weekday == weekday))
            .order_by(MasterSchedule.time_from)
        )
        return result.scalars().all()

    async def get_by_weekday(self, weekday: int, skip: int = 0, limit: int = 100) -> List[MasterSchedule]:
        """Получить все расписания на конкретный день недели"""
        result = await self.db.execute(
            select(MasterSchedule)
            .where(MasterSchedule.weekday == weekday)
            .offset(skip)
            .limit(limit)
            .order_by(MasterSchedule.master_id, MasterSchedule.time_from)
        )
        return result.scalars().all()

    async def check_time_conflict(
        self, 
        master_id: int, 
        weekday: int, 
        time_from, 
        time_to, 
        exclude_schedule_id: Optional[int] = None
    ) -> bool:
        """Проверить конфликт времени в расписании"""
        query = select(MasterSchedule).where(
            and_(
                MasterSchedule.master_id == master_id,
                MasterSchedule.weekday == weekday,
                or_(
                    and_(MasterSchedule.time_from <= time_from, MasterSchedule.time_to > time_from),
                    and_(MasterSchedule.time_from < time_to, MasterSchedule.time_to >= time_to),
                    and_(MasterSchedule.time_from >= time_from, MasterSchedule.time_to <= time_to)
                )
            )
        )
        
        if exclude_schedule_id:
            query = query.where(MasterSchedule.id != exclude_schedule_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(self, schedule_create: MasterScheduleCreate) -> MasterSchedule:
        """Создать расписание мастера"""
        db_schedule = MasterSchedule(**schedule_create.model_dump())
        self.db.add(db_schedule)
        await self.db.commit()
        await self.db.refresh(db_schedule)
        return db_schedule

    async def create_multiple(self, master_id: int, schedules: List[MasterScheduleCreate]) -> List[MasterSchedule]:
        """Создать несколько расписаний для мастера"""
        db_schedules = []
        for schedule_data in schedules:
            schedule = MasterSchedule(
                master_id=master_id,
                weekday=schedule_data.weekday,
                time_from=schedule_data.time_from,
                time_to=schedule_data.time_to
            )
            self.db.add(schedule)
            db_schedules.append(schedule)
        
        await self.db.commit()
        for schedule in db_schedules:
            await self.db.refresh(schedule)
        
        return db_schedules

    async def update(self, schedule_id: int, schedule_update: MasterScheduleUpdate) -> Optional[MasterSchedule]:
        """Обновить расписание"""
        db_schedule = await self.get(schedule_id)
        if not db_schedule:
            return None
        
        update_data = schedule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_schedule)
        return db_schedule

    async def delete(self, schedule_id: int) -> bool:
        """Удалить расписание"""
        db_schedule = await self.get(schedule_id)
        if not db_schedule:
            return False
        
        await self.db.delete(db_schedule)
        await self.db.commit()
        return True

    async def delete_by_master_id(self, master_id: int) -> bool:
        """Удалить все расписания мастера"""
        result = await self.db.execute(
            delete(MasterSchedule).where(MasterSchedule.master_id == master_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_with_relations(self, schedule_id: int) -> Optional[MasterSchedule]:
        """Получить расписание со связанными данными"""
        result = await self.db.execute(
            select(MasterSchedule)
            .options(selectinload(MasterSchedule.master))
            .where(MasterSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()


# Dependency function
def get_master_schedule_crud(db: AsyncSession) -> MasterScheduleCRUD:
    return MasterScheduleCRUD(db)
