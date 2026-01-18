from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.user import User, UserRoleEnum
from telegram_bot_app.schemas.user import UserCreate, UserUpdate

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from telegram_bot_app.models.user import User, UserRoleEnum
from telegram_bot_app.schemas.user import UserCreate, UserUpdate


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить всех пользователей с пагинацией"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_role(self, role: UserRoleEnum, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить пользователей по роли"""
        result = await self.db.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_masters(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить активных мастеров"""
        result = await self.db.execute(
            select(User)
            .where(and_(User.role == UserRoleEnum.MASTER, User.is_active == True))
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, user_create: UserCreate) -> User:
        """Создать нового пользователя"""
        db_user = User(**user_create.model_dump())
        self.db.add(db_user)
        await self.db.flush()  # flush вместо commit
        return db_user

    async def update(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Обновить данные пользователя"""
        db_user = await self.get(user_id)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        await self.db.flush()  # flush вместо commit
        return db_user

    async def delete(self, user_id: int) -> bool:
        """Удалить пользователя"""
        db_user = await self.get(user_id)
        if not db_user:
            return False

        await self.db.delete(db_user)
        await self.db.flush()  # flush вместо commit
        return True

    async def get_with_relations(self, user_id: int) -> Optional[User]:
        """Получить пользователя со связанными данными"""
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.master_profile),
                selectinload(User.appointments_as_client)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# Dependency function
def get_user_crud(db: AsyncSession) -> UserCRUD:
    return UserCRUD(db)


# Dependency function
def get_user_crud(db: AsyncSession) -> UserCRUD:
    return UserCRUD(db)
