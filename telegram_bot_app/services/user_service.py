from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_bot_app.models.user import User, UserRoleEnum
from telegram_bot_app.crud.user import UserCRUD

import logging
logger = logging.getLogger(__name__)

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
        """Найти или создать пользователя"""

        try:
            # Проверяем, существует ли пользователь
            user = await self.user_crud.get_by_telegram_id(telegram_id)
            
            logger.info(f"🔍 Результат поиска пользователя: {user}")

            if user is not None:
                logger.info(
                    "✅ Пользователь найден: user_id=%d, telegram_id=%d",
                    user.id, telegram_id
                )
                return user

            # Дополнительная проверка через прямой SQL запрос
            logger.info("🔄 Дополнительная проверка через SQL...")
            from sqlalchemy import text
            result = await self.db.execute(
                text("SELECT id, telegram_id, full_name FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_id}
            )
            sql_user = result.fetchone()
            logger.info(f"🔍 SQL результат: {sql_user}")
            
            if sql_user:
                logger.info("✅ Пользователь найден через SQL, создаем объект")
                user = User(
                    id=sql_user[0],
                    telegram_id=sql_user[1], 
                    full_name=sql_user[2],
                    role=UserRoleEnum.CLIENT,
                    is_active=True
                )
                return user

            # Создаем нового пользователя
            logger.info("🆕 Создание нового пользователя...")
            new_user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                role=role,
                is_active=True
            )

            self.db.add(new_user)
            await self.db.commit()  # Используем commit вместо flush
            await self.db.refresh(new_user)  # Получаем ID из БД

            logger.info(
                "✅ Создан новый пользователь: user_id=%d, telegram_id=%d, name=%s",
                new_user.id, telegram_id, full_name
            )

            return new_user

        except Exception as e:
            logger.error(
                "❌ Ошибка создания/получения пользователя telegram_id=%d: %s",
                telegram_id, e, exc_info=True
            )
            await self.db.rollback()  # Откатываем транзакцию при ошибке
            raise

    async def create_user_without_telegram(
            self,
            full_name: str,
            role: UserRoleEnum = UserRoleEnum.MASTER
    ) -> User:
        """Создать пользователя без Telegram ID (например, мастера)."""

        logger.info(
            "Создание пользователя без Telegram: name=%s, role=%s",
            full_name, role
        )

        try:
            new_user = User(
                telegram_id=None,
                full_name=full_name,
                role=role,
                is_active=True
            )

            self.db.add(new_user)
            await self.db.commit()  # Используем commit вместо flush
            await self.db.refresh(new_user)  # Получаем ID из БД

            logger.info(
                "✅ Создан пользователь (без Telegram): user_id=%d, name=%s",
                new_user.id, full_name
            )

            return new_user

        except Exception as e:
            logger.error(
                "❌ Ошибка создания пользователя без Telegram: %s",
                e, exc_info=True
            )
            await self.db.rollback()  # Откатываем транзакцию при ошибке
            raise

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        logger.debug("Поиск пользователя по telegram_id=%d", telegram_id)

        try:
            user = await self.user_crud.get_by_telegram_id(telegram_id)

            if user:
                logger.debug(
                    "Пользователь найден: user_id=%d, telegram_id=%d",
                    user.id, telegram_id
                )
            else:
                logger.debug("Пользователь не найден: telegram_id=%d", telegram_id)

            return user

        except Exception as e:
            logger.error(
                "Ошибка поиска пользователя telegram_id=%d: %s",
                telegram_id, e, exc_info=True
            )
            return None

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        logger.debug("Поиск пользователя по user_id=%d", user_id)

        try:
            user = await self.user_crud.get(user_id)

            if user:
                logger.debug("Пользователь найден: user_id=%d", user_id)
            else:
                logger.debug("Пользователь не найден: user_id=%d", user_id)

            return user

        except Exception as e:
            logger.error(
                "Ошибка поиска пользователя user_id=%d: %s",
                user_id, e, exc_info=True
            )
            return None