import asyncio
from datetime import datetime, timedelta
import logging
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select, and_
from telegram_bot_app.celery_app.celery import celery_app
from telegram_bot_app.core.config import settings
from telegram_bot_app.db.base import async_session
from telegram_bot_app.models.appointment import Appointment, AppointmentStatusEnum

# Создаем логгер
logger = logging.getLogger(__name__)


def run_async(coro):
    """Запуск асинхронной функции в Celery worker"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


@celery_app.task(name="telegram_bot_app.celery_app.tasks.send_appointment_confirmation")
def send_appointment_confirmation(appointment_id: int):
    """
    Отправка подтверждения создания записи
    """
    return run_async(_send_confirmation_async(appointment_id))


async def _send_confirmation_async(appointment_id: int, bot: Bot = None):
    """Асинхронная отправка подтверждения"""
    logger.info("Отправка подтверждения для записи #%d", appointment_id)

    # Используем переданный бот или создаем новый
    if bot is None:
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )

    try:
        async with async_session() as db:
            result = await db.execute(
                select(Appointment)
                .where(Appointment.id == appointment_id)
            )
            appointment = result.scalar_one_or_none()

            if not appointment or not appointment.client:
                logger.warning("Запись #%d не найдена или нет клиента", appointment_id)
                return

            # Форматирование даты
            months = {
                1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
            }
            formatted_date = f"{appointment.date.day} {months[appointment.date.month]}"

            # Формируем адрес с ссылкой на 2GIS если доступна
            if appointment.salon.gis_link:
                address_text = f"📍 Адрес: [Посмотреть на карте]({appointment.salon.gis_link})"
            else:
                address_text = f"📍 Адрес: {appointment.salon.address}"

            # Проверяем, нужно ли показывать уведомление за 1 час
            now = datetime.now()
            appointment_datetime = datetime.combine(appointment.date, appointment.time_start)
            time_diff = appointment_datetime - now
            time_diff_minutes = time_diff.total_seconds() / 60

            # Формируем сообщение в зависимости от времени до записи
            if time_diff_minutes < 59:
                # Если до записи меньше 59 минут, не показываем уведомление за 1 час
                message = (
                    f"✅ *Запись подтверждена!*\n\n"
                    f"📋 Номер записи: #{appointment.id}\n"
                    f"🏛️ Салон: {appointment.salon.name}\n"
                    f"✨ Услуга: {appointment.service.name}\n"
                    f"👨‍💼 Мастер: {appointment.master.user.full_name}\n"
                    f"📅 Дата: {formatted_date}\n"
                    f"🕐 Время: {appointment.time_start.strftime('%H:%M')}\n"
                    f"💰 Стоимость: {appointment.service.price} тг.\n"
                    f"{address_text}\n\n"
                    f"Ждем вас! 😊"
                )
            else:
                # Если до записи 59 минут или больше, показываем уведомление за 1 час
                message = (
                    f"✅ *Запись подтверждена!*\n\n"
                    f"📋 Номер записи: #{appointment.id}\n"
                    f"🏛️ Салон: {appointment.salon.name}\n"
                    f"✨ Услуга: {appointment.service.name}\n"
                    f"👨‍💼 Мастер: {appointment.master.user.full_name}\n"
                    f"📅 Дата: {formatted_date}\n"
                    f"🕐 Время: {appointment.time_start.strftime('%H:%M')}\n"
                    f"💰 Стоимость: {appointment.service.price} тг.\n"
                    f"{address_text}\n\n"
                    f"Ждем вас! За 1 час до записи придет напоминание 🔔"
                )

            await bot.send_message(
                chat_id=appointment.client.telegram_id,
                text=message
            )

            logger.info(
                "✅ Подтверждение отправлено: appointment_id=%d, client_id=%d",
                appointment_id, appointment.client.telegram_id
            )

    except Exception as e:
        logger.error(
            "Ошибка отправки подтверждения для записи #%d: %s",
            appointment_id, e, exc_info=True
        )
    finally:
        await bot.session.close()


@celery_app.task(name="telegram_bot_app.celery_app.tasks.send_appointment_reminders")
def send_appointment_reminders(minutes_before: int = None, hours_before: int = None):
    """
    Отправка напоминаний о предстоящих записях

    Args:
        minutes_before: за сколько минут до записи отправлять
        hours_before: за сколько часов до записи отправлять (24 или 1)
    """
    return run_async(_send_reminders_async(minutes_before=minutes_before, hours_before=hours_before))


async def _send_reminders_async(minutes_before: int = None, hours_before: int = None):
    """Асинхронная отправка напоминаний о записи за N минут/часов до начала"""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    try:
        now = datetime.now()

        # Определяем за сколько минут до записи отправлять
        if minutes_before is not None:
            target_minutes = minutes_before
            reminder_text = f"через {minutes_before} минут" if minutes_before > 1 else "через 1 минуту"
            emoji = "⏰"
        elif hours_before is not None:
            target_minutes = hours_before * 60
            if hours_before == 1:
                reminder_text = "через 1 час"
            elif hours_before == 24:
                reminder_text = "завтра"
            else:
                reminder_text = f"через {hours_before} часа"
            emoji = "📅" if hours_before == 24 else "⏰"
        else:
            return

        # Вычисляем целевое время записи
        target_appointment_time = now + timedelta(minutes=target_minutes)
        window_start = target_appointment_time - timedelta(seconds=30)
        window_end = target_appointment_time + timedelta(seconds=30)

        logger.info(
            "Проверка напоминаний за %d минут (target: %s)",
            target_minutes, target_appointment_time.strftime('%Y-%m-%d %H:%M:%S')
        )

        async with async_session() as db:
            # Получаем все BOOKED записи на целевую дату
            result = await db.execute(
                select(Appointment)
                .where(
                    and_(
                        Appointment.status == AppointmentStatusEnum.BOOKED,
                        Appointment.date == target_appointment_time.date()
                    )
                )
            )
            all_appointments = result.scalars().all()

            logger.debug(
                "Найдено %d записей на %s",
                len(all_appointments), target_appointment_time.date()
            )

            sent_count = 0
            for apt in all_appointments:
                if not apt.client:
                    continue

                # Собираем полный datetime записи
                appointment_datetime = datetime.combine(apt.date, apt.time_start)

                # Проверяем попадает ли в окно
                if window_start <= appointment_datetime <= window_end:
                    logger.info(
                        "Отправка напоминания: appointment_id=%d, client_id=%d, время=%s",
                        apt.id, apt.client.telegram_id, apt.time_start
                    )

                    # Форматирование даты
                    months = {
                        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
                    }
                    formatted_date = f"{apt.date.day} {months[apt.date.month]}"

                    # Формируем адрес с ссылкой на 2GIS если доступна
                    if apt.salon.gis_link:
                        address_text = f"📍 Адрес: [Посмотреть на карте]({apt.salon.gis_link})"
                    else:
                        address_text = f"📍 Адрес: {apt.salon.address}"

                    message = (
                        f"{emoji} *Напоминание о записи {reminder_text}!*\n\n"
                        f"📋 Номер: #{apt.id}\n"
                        f"🏛️ Салон: {apt.salon.name}\n"
                        f"✨ Услуга: {apt.service.name}\n"
                        f"👨‍💼 Мастер: {apt.master.user.full_name}\n"
                        f"📅 Дата: {formatted_date}\n"
                        f"🕐 Время: {apt.time_start.strftime('%H:%M')}\n"
                        f"{address_text}\n\n"
                        f"Ждем вас! 😊"
                    )

                    try:
                        await bot.send_message(
                            chat_id=apt.client.telegram_id,
                            text=message
                        )
                        logger.info("✅ Напоминание отправлено для записи #%d", apt.id)
                        sent_count += 1
                    except Exception as e:
                        logger.error(
                            "Ошибка отправки напоминания для записи #%d: %s",
                            apt.id, e
                        )

            if sent_count > 0:
                logger.info("Отправлено напоминаний: %d", sent_count)
            else:
                logger.debug("Записей для напоминания не найдено")

    except Exception as e:
        logger.error("Ошибка в send_reminders: %s", e, exc_info=True)
    finally:
        await bot.session.close()


@celery_app.task(name="telegram_bot_app.celery_app.tasks.send_cancellation_notification")
def send_cancellation_notification(appointment_id: int, client_telegram_id: int):
    """
    Уведомление об отмене записи
    """
    return run_async(_send_cancellation_async(appointment_id, client_telegram_id))


async def _send_cancellation_async(appointment_id: int, client_telegram_id: int, bot: Bot = None):
    """Асинхронная отправка уведомления об отмене"""
    logger.info("Отправка уведомления об отмене записи #%d", appointment_id)

    # Используем переданный бот или создаем новый
    if bot is None:
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )

    try:
        message = (
            f"❌ *Запись #{appointment_id} отменена*\n\n"
            f"Вы можете создать новую запись в любое время.\n"
            f"Для этого нажмите кнопку '➕ Создать запись'"
        )

        await bot.send_message(
            chat_id=client_telegram_id,
            text=message
        )
        logger.info(
            "✅ Уведомление об отмене отправлено: appointment_id=%d, client_id=%d",
            appointment_id, client_telegram_id
        )

    except Exception as e:
        logger.error(
            "Ошибка отправки уведомления об отмене для записи #%d: %s",
            appointment_id, e, exc_info=True
        )
    finally:
        await bot.session.close()