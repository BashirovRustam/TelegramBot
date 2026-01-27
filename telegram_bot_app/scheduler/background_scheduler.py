import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, and_
from telegram_bot_app.db.base import async_session as async_session_maker
from telegram_bot_app.models.appointment import Appointment, AppointmentStatusEnum
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


class AppointmentNotificationScheduler:
    """
    Фоновый планировщик для отправки уведомлений о записях за 1 час
    Использует polling БД каждые N минут
    """

    def __init__(self, bot: Bot, check_interval_minutes: int = 1, notify_hours_before: int = 1,
                 timezone: str = "Asia/Almaty"):
        """
        Args:
            bot: Экземпляр aiogram Bot
            check_interval_minutes: Интервал проверки БД в минутах
            notify_hours_before: За сколько часов до записи отправлять уведомление
            timezone: Часовой пояс для работы с записями (например, 'Asia/Almaty', 'Europe/Moscow')
        """
        self.bot = bot
        self.check_interval = check_interval_minutes * 60  # в секундах
        self.notify_hours_before = notify_hours_before
        self.timezone = ZoneInfo(timezone)
        self.is_running = False
        self._task = None

    async def start(self):
        """Запуск фонового планировщика"""
        if self.is_running:
            logger.warning("⚠️ Scheduler is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(
            f"✅ Notification scheduler started "
            f"(notify {self.notify_hours_before}h before, checking every {self.check_interval}s)"
        )

    async def stop(self):
        """Остановка фонового планировщика"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Notification scheduler stopped")

    async def _run_scheduler(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                logger.info(f"🔄 Scheduler check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await self._check_and_send_notifications()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("📌 Scheduler task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # При ошибке ждем 1 минуту

    async def _check_and_send_notifications(self):
        """
        Проверка БД и отправка уведомлений

        Логика:
        1. Находим все записи, которые еще не уведомлены
        2. Проверяем, что до записи осталось примерно 1 час (±интервал проверки)
        3. Отправляем уведомление и отмечаем как notified
        """
        try:
            async with async_session_maker() as session:
                # Получаем текущее время в нужном часовом поясе
                now = datetime.now(self.timezone)

                # Вычисляем временное окно для уведомлений
                # Ищем записи, которые начнутся примерно через 1 час от текущего времени
                margin_minutes = 3  # Окно в ±3 минуты для надежного уведомления

                # Время, через которое должна начаться запись
                target_appointment_time = now + timedelta(hours=self.notify_hours_before)

                # Окно для поиска записей
                target_time_start = target_appointment_time - timedelta(minutes=margin_minutes)
                target_time_end = target_appointment_time + timedelta(minutes=margin_minutes)

                logger.info(
                    f"🔍 Checking appointments between "
                    f"{target_time_start.strftime('%Y-%m-%d %H:%M')} and "
                    f"{target_time_end.strftime('%Y-%m-%d %H:%M')} "
                    f"(current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')})"
                )

                # Находим записи, которые не уведомлены и со статусом BOOKED
                query = select(Appointment).where(
                    and_(
                        Appointment.status == AppointmentStatusEnum.BOOKED,
                        Appointment.notified == False
                    )
                )

                result = await session.execute(query)
                appointments = result.scalars().all()

                if not appointments:
                    logger.info("📭 No pending appointments in database")
                    return

                logger.info(f"📋 Found {len(appointments)} pending appointments to check")

                # Фильтруем записи по времени
                notifications_sent = 0
                notifications_failed = 0

                for appointment in appointments:
                    # Создаем datetime для записи в нужном часовом поясе
                    appointment_datetime = datetime.combine(
                        appointment.date,
                        appointment.time_start,
                        tzinfo=self.timezone
                    )

                    logger.info(
                        f"🔍 Checking appointment #{appointment.id} at {appointment_datetime.strftime('%Y-%m-%d %H:%M %Z')}")

                    # Проверяем, попадает ли запись в целевое окно
                    if target_time_start <= appointment_datetime <= target_time_end:
                        logger.info(f"⏰ Appointment #{appointment.id} is in notification window!")
                        try:
                            await self._send_notification(appointment, session)
                            notifications_sent += 1
                        except Exception as e:
                            notifications_failed += 1
                            logger.error(f"❌ Failed to send notification for appointment #{appointment.id}: {e}")
                    else:
                        logger.info(f"⏭️ Appointment #{appointment.id} not in notification window")

                if notifications_sent > 0:
                    logger.info(f"📬 Sent {notifications_sent} notification(s)")
                if notifications_failed > 0:
                    logger.warning(f"⚠️ Failed to send {notifications_failed} notification(s)")
                if notifications_sent == 0 and notifications_failed == 0:
                    logger.debug(f"📭 No appointments in notification window (checked {len(appointments)} appointments)")

        except Exception as e:
            logger.error(f"❌ Error checking notifications: {e}", exc_info=True)

    async def _send_notification(self, appointment: Appointment, session):
        """
        Отправка уведомления конкретному клиенту
        """
        try:
            # Вычисляем точное время до записи
            appointment_datetime = datetime.combine(
                appointment.date,
                appointment.time_start,
                tzinfo=self.timezone
            )
            now = datetime.now(self.timezone)
            time_until = appointment_datetime - now
            hours_left = int(time_until.total_seconds() // 3600)
            minutes_left = int((time_until.total_seconds() % 3600) // 60)

            # Формируем сообщение
            time_message = ""
            if hours_left > 0:
                time_message = f"Через {hours_left} ч {minutes_left} мин"
            else:
                time_message = f"Через {minutes_left} минут"

            message = (
                f"🔔 *Напоминание о записи\\!*\n\n"
                f"⏰ {time_message} у вас запись:\n\n"
                f"📅 *Дата:* {appointment.date.strftime('%d\\.%m\\.%Y')}\n"
                f"🕐 *Время:* {appointment.time_start.strftime('%H:%M')}\n"
                f"💇 *Услуга:* {self._escape_markdown(appointment.service.name)}\n"
                f"👤 *Мастер:* {self._escape_markdown(str(appointment.master))}\n"
                f"🏢 *Салон:* {self._escape_markdown(appointment.salon.name)}\n"
                f"📍 *Адрес:* {self._escape_markdown(appointment.salon.address)}\n\n"
                f"✨ Ждем вас\\!"
            )

            # Создаем клавиатуру с кнопкой 2GIS если ссылка доступна
            keyboard = None
            if appointment.salon.gis_link:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📍 Показать на карте", url=appointment.salon.gis_link)]
                ])

            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=appointment.client.telegram_id,
                text=message,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )

            # Отмечаем как уведомленное
            appointment.notified = True
            await session.commit()

            logger.info(
                f"✅ Notification sent for appointment #{appointment.id} "
                f"to user {appointment.client_id} "
                f"(appointment at {appointment_datetime.strftime('%Y-%m-%d %H:%M %Z')})"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to send notification for appointment #{appointment.id}: {e}",
                exc_info=True
            )
            # Если пользователь заблокировал бота, отмечаем как уведомленное чтобы не пытаться снова
            if "chat not found" in str(e).lower() or "bad request: chat not found" in str(e).lower():
                logger.info(
                    f"🚫 User {appointment.client_id} has blocked the bot or chat not found. Marking as notified.")
                appointment.notified = True
                await session.commit()
            # Не коммитим изменения для других ошибок, чтобы попробовать еще раз при следующей проверке

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Экранирование спецсимволов для MarkdownV2"""
        # Удаляем невидимые символы
        text = text.replace('\u200B', '')  # zero-width space
        text = text.replace('\u200C', '')  # zero-width non-joiner
        text = text.replace('\u200D', '')  # zero-width joiner
        text = text.replace('\uFEFF', '')  # zero-width no-break space

        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text