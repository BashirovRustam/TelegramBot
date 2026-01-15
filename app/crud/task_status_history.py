from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.task_status_history import TaskStatusHistory
from app.db.enums import TaskStatusEnum
from app.schemas.task_status import TaskStatusHistoryCreate, TaskStatusHistoryUpdate


class TaskStatusCRUD:
    """CRUD сервис для работы с историей статусов задач"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией SQLAlchemy
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def create(self, status_data: TaskStatusHistoryCreate) -> TaskStatusHistory:
        """
        Создает запись об изменении статуса задачи
        
        Args:
            status_data: Pydantic схема с данными для создания записи истории
            
        Returns:
            Созданная запись истории (ORM объект)
        """
        status_change = TaskStatusHistory(
            task_id=status_data.task_id,
            old_status=status_data.old_status,
            new_status=status_data.new_status,
            changed_by=status_data.changed_by
        )
        self.session.add(status_change)
        await self.session.commit()
        await self.session.refresh(status_change)
        return status_change

    async def get(self, history_id: int) -> Optional[TaskStatusHistory]:
        """
        Получает запись истории по ID
        
        Args:
            history_id: ID записи истории
            
        Returns:
            Найденная запись или None
        """
        stmt = select(TaskStatusHistory).where(TaskStatusHistory.id == history_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[TaskStatusHistory]:
        """
        Получает список всех записей истории
        
        Returns:
            Список всех записей истории (ORM объекты)
        """
        stmt = select(TaskStatusHistory).order_by(TaskStatusHistory.changed_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_task(self, task_id: int) -> List[TaskStatusHistory]:
        """
        Получает историю изменений статусов для указанной задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Список записей истории для задачи
        """
        stmt = (
            select(TaskStatusHistory)
            .where(TaskStatusHistory.task_id == task_id)
            .order_by(TaskStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, user_id: int) -> List[TaskStatusHistory]:
        """
        Получает историю изменений, сделанных указанным пользователем
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список записей истории пользователя
        """
        stmt = (
            select(TaskStatusHistory)
            .where(TaskStatusHistory.changed_by == user_id)
            .order_by(TaskStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(
        self, status: TaskStatusEnum
    ) -> List[TaskStatusHistory]:
        """
        Получает записи истории с указанным новым статусом
        
        Args:
            status: Статус задачи
            
        Returns:
            Список записей с указанным статусом
        """
        stmt = (
            select(TaskStatusHistory)
            .where(TaskStatusHistory.new_status == status)
            .order_by(TaskStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_by_task(self, task_id: int) -> Optional[TaskStatusHistory]:
        """
        Получает последнюю запись истории для задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Последняя запись истории или None
        """
        stmt = (
            select(TaskStatusHistory)
            .where(TaskStatusHistory.task_id == task_id)
            .order_by(TaskStatusHistory.changed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, history_id: int, status_data: TaskStatusHistoryUpdate) -> Optional[TaskStatusHistory]:
        """
        Обновляет данные записи истории (частичное обновление)
        
        Args:
            history_id: ID записи истории
            status_data: Pydantic схема с данными для обновления
            
        Returns:
            Обновленная запись или None
        """
        # Получаем только установленные поля из Pydantic схемы
        update_data = status_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get(history_id)
        
        stmt = (
            update(TaskStatusHistory)
            .where(TaskStatusHistory.id == history_id)
            .values(**update_data)
            .returning(TaskStatusHistory)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get(history_id)

    async def delete(self, history_id: int) -> bool:
        """
        Удаляет запись истории
        
        Args:
            history_id: ID записи истории
            
        Returns:
            True если запись была удалена, иначе False
        """
        stmt = delete(TaskStatusHistory).where(TaskStatusHistory.id == history_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_by_task(self, task_id: int) -> int:
        """
        Удаляет всю историю для указанной задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Количество удаленных записей
        """
        stmt = delete(TaskStatusHistory).where(TaskStatusHistory.task_id == task_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_with_relations(self, history_id: int) -> Optional[TaskStatusHistory]:
        """
        Получает запись истории с загруженными связанными данными
        
        Args:
            history_id: ID записи истории
            
        Returns:
            Запись с загруженными связями или None
        """
        stmt = (
            select(TaskStatusHistory)
            .options(
                selectinload(TaskStatusHistory.task),
                selectinload(TaskStatusHistory.user)
            )
            .where(TaskStatusHistory.id == history_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_task(self, task_id: int) -> int:
        """
        Подсчитывает количество записей истории для задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Количество записей истории
        """
        stmt = select(TaskStatusHistory).where(TaskStatusHistory.task_id == task_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def get_status_changes_in_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[TaskStatusHistory]:
        """
        Получает записи истории за указанный период
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            Список записей за период
        """
        stmt = (
            select(TaskStatusHistory)
            .where(
                TaskStatusHistory.changed_at >= start_date,
                TaskStatusHistory.changed_at <= end_date
            )
            .order_by(TaskStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
