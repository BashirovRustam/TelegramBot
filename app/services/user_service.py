from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.users import User
from app.db.enums import RolesEnum
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """CRUD сервис для работы с пользователями"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией SQLAlchemy
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        """
        Создает нового пользователя
        
        Args:
            user_data: Pydantic схема с данными для создания пользователя
            
        Returns:
            Созданный пользователь (ORM объект)
        """
        user = User(
            telegram_id=user_data.telegram_id,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Найденный пользователь или None
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получает пользователя по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Найденный пользователь или None
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[User]:
        """
        Получает список всех пользователей
        
        Returns:
            Список всех пользователей (ORM объекты)
        """
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_users(self) -> List[User]:
        """
        Получает список активных пользователей
        
        Returns:
            Список активных пользователей (ORM объекты)
        """
        stmt = select(User).where(User.is_active == True).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Обновляет данные пользователя (частичное обновление)
        
        Args:
            user_id: ID пользователя
            user_data: Pydantic схема с данными для обновления
            
        Returns:
            Обновленный пользователь или None
        """
        # Получаем только установленные поля из Pydantic схемы
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return await self.get(user_id)
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get(user_id)

    async def delete(self, user_id: int) -> bool:
        """
        Удаляет пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если пользователь был удален, иначе False
        """
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_with_relations(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя со всеми связанными данными
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Пользователь с загруженными связями или None
        """
        stmt = (
            select(User)
            .options(
                selectinload(User.tasks_created),
                selectinload(User.tasks_assigned),
                selectinload(User.status_changes)
            )
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
