from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from telegram_bot_app.models.user import User, UserRoleEnum
from telegram_bot_app.crud.user import UserCRUD


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = UserCRUD(db)

    async def get_or_create_user(
            self,
            telegram_id: int,
            full_name: str,
            role: UserRoleEnum = UserRoleEnum.CLIENT
    ) -> User:
        """
        Получить пользователя или создать, если не существует.

        Args:
            telegram_id: Telegram ID пользователя
            full_name: Полное имя пользователя
            role: Роль пользователя (по умолчанию CLIENT)

        Returns:
            User: Объект пользователя
        """
        # Проверяем, существует ли пользователь
        user = await self.user_crud.get_by_telegram_id(telegram_id)

        if user:
            return user

        # Создаем нового пользователя (ID автогенерируется)
        new_user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            role=role,
            is_active=True
        )

        self.db.add(new_user)
        await self.db.flush()  # flush вместо commit

        return new_user

    async def create_user_without_telegram(
            self,
            full_name: str,
            role: UserRoleEnum = UserRoleEnum.MASTER
    ) -> User:
        """
        Создать пользователя без Telegram ID (например, мастера).

        Args:
            full_name: Полное имя пользователя
            role: Роль пользователя (по умолчанию MASTER)

        Returns:
            User: Объект пользователя
        """
        new_user = User(
            telegram_id=None,  # Нет Telegram ID
            full_name=full_name,
            role=role,
            is_active=True
        )

        self.db.add(new_user)
        await self.db.flush()

        return new_user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return await self.user_crud.get_by_telegram_id(telegram_id)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_crud.get(user_id)