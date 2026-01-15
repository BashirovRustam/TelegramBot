from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.task_attachment import TaskAttachment
from app.schemas.task_control import TaskAttachmentCreate, TaskAttachmentUpdate


class TaskControlCRUD:
    """CRUD сервис для работы с вложениями задач"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией SQLAlchemy
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def create(self, attachment_data: TaskAttachmentCreate) -> TaskAttachment:
        """
        Создает новое вложение для задачи
        
        Args:
            attachment_data: Pydantic схема с данными для создания вложения
            
        Returns:
            Созданное вложение (ORM объект)
        """
        attachment = TaskAttachment(
            task_id=attachment_data.task_id,
            telegram_file_id=attachment_data.telegram_file_id
        )
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment

    async def get(self, attachment_id: int) -> Optional[TaskAttachment]:
        """
        Получает вложение по ID
        
        Args:
            attachment_id: ID вложения
            
        Returns:
            Найденное вложение или None
        """
        stmt = select(TaskAttachment).where(TaskAttachment.id == attachment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[TaskAttachment]:
        """
        Получает список всех вложений
        
        Returns:
            Список всех вложений (ORM объекты)
        """
        stmt = select(TaskAttachment).order_by(TaskAttachment.uploaded_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_task(self, task_id: int) -> List[TaskAttachment]:
        """
        Получает все вложения для указанной задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Список вложений задачи
        """
        stmt = (
            select(TaskAttachment)
            .where(TaskAttachment.task_id == task_id)
            .order_by(TaskAttachment.uploaded_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_telegram_file_id(
        self, telegram_file_id: str
    ) -> Optional[TaskAttachment]:
        """
        Получает вложение по Telegram file ID
        
        Args:
            telegram_file_id: ID файла в Telegram
            
        Returns:
            Найденное вложение или None
        """
        stmt = select(TaskAttachment).where(TaskAttachment.telegram_file_id == telegram_file_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, attachment_id: int, attachment_data: TaskAttachmentUpdate) -> Optional[TaskAttachment]:
        """
        Обновляет данные вложения (частичное обновление)
        
        Args:
            attachment_id: ID вложения
            attachment_data: Pydantic схема с данными для обновления
            
        Returns:
            Обновленное вложение или None
        """
        # Получаем только установленные поля из Pydantic схемы
        update_data = attachment_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get(attachment_id)
        
        stmt = (
            update(TaskAttachment)
            .where(TaskAttachment.id == attachment_id)
            .values(**update_data)
            .returning(TaskAttachment)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get(attachment_id)

    async def delete(self, attachment_id: int) -> bool:
        """
        Удаляет вложение
        
        Args:
            attachment_id: ID вложения
            
        Returns:
            True если вложение было удалено, иначе False
        """
        stmt = delete(TaskAttachment).where(TaskAttachment.id == attachment_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_by_task(self, task_id: int) -> int:
        """
        Удаляет все вложения для указанной задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Количество удаленных вложений
        """
        stmt = delete(TaskAttachment).where(TaskAttachment.task_id == task_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_with_task(self, attachment_id: int) -> Optional[TaskAttachment]:
        """
        Получает вложение с загруженной связанной задачей
        
        Args:
            attachment_id: ID вложения
            
        Returns:
            Вложение с загруженной задачей или None
        """
        stmt = (
            select(TaskAttachment)
            .options(selectinload(TaskAttachment.task))
            .where(TaskAttachment.id == attachment_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_task(self, task_id: int) -> int:
        """
        Подсчитывает количество вложений для задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Количество вложений
        """
        stmt = select(TaskAttachment).where(TaskAttachment.task_id == task_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
