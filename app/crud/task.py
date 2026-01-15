from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.db.enums import TaskStatusEnum
from app.schemas.task import TaskCreate, TaskUpdate


class TaskCRUD:
    """CRUD сервис для работы с задачами"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией SQLAlchemy
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def create(self, task_data: TaskCreate) -> Task:
        """
        Создает новую задачу
        
        Args:
            task_data: Pydantic схема с данными для создания задачи
            
        Returns:
            Созданная задача (ORM объект)
        """
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            start_date=task_data.start_date,
            deadline=task_data.deadline,
            executor_id=task_data.executor_id,
            created_by=task_data.created_by
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        """
        Получает задачу по ID
        
        Args:
            task_id: ID задачи
            
        Returns:
            Найденная задача или None
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Task]:
        """
        Получает список всех задач
        
        Returns:
            Список всех задач (ORM объекты)
        """
        stmt = select(Task).order_by(Task.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_creator(self, creator_id: int) -> List[Task]:
        """
        Получает задачи, созданные указанным пользователем
        
        Args:
            creator_id: ID создателя
            
        Returns:
            Список задач создателя
        """
        stmt = (
            select(Task)
            .where(Task.created_by == creator_id)
            .order_by(Task.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_executor(self, executor_id: int) -> List[Task]:
        """
        Получает задачи, назначенные на указанного исполнителя
        
        Args:
            executor_id: ID исполнителя
            
        Returns:
            Список задач исполнителя
        """
        stmt = (
            select(Task)
            .where(Task.executor_id == executor_id)
            .order_by(Task.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(self, status: TaskStatusEnum) -> List[Task]:
        """
        Получает задачи по статусу
        
        Args:
            status: Статус задачи
            
        Returns:
            Список задач с указанным статусом
        """
        stmt = (
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Обновляет данные задачи (частичное обновление)
        
        Args:
            task_id: ID задачи
            task_data: Pydantic схема с данными для обновления
            
        Returns:
            Обновленная задача или None
        """
        # Получаем только установленные поля из Pydantic схемы
        update_data = task_data.model_dump(exclude_unset=True)
        
        # Если статус меняется на COMPLETED, устанавливаем completed_at
        if 'status' in update_data and update_data['status'] == TaskStatusEnum.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
        
        if not update_data:
            return await self.get(task_id)
        
        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(**update_data)
            .returning(Task)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get(task_id)

    async def delete(self, task_id: int) -> bool:
        """
        Удаляет задачу
        
        Args:
            task_id: ID задачи
            
        Returns:
            True если задача была удалена, иначе False
        """
        stmt = delete(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_with_relations(self, task_id: int) -> Optional[Task]:
        """
        Получает задачу со всеми связанными данными
        
        Args:
            task_id: ID задачи
            
        Returns:
            Задача с загруженными связями или None
        """
        stmt = (
            select(Task)
            .options(
                selectinload(Task.creator),
                selectinload(Task.executor),
                selectinload(Task.attachments),
                selectinload(Task.status_history)
            )
            .where(Task.id == task_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_overdue_tasks(self) -> List[Task]:
        """
        Получает просроченные задачи
        
        Returns:
            Список просроченных задач
        """
        today = date.today()
        stmt = (
            select(Task)
            .where(
                Task.deadline < today,
                Task.status != TaskStatusEnum.COMPLETED
            )
            .order_by(Task.deadline.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
