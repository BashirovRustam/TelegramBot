import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select, and_
from telegram_bot_app.celery_app.celery import celery_app
from telegram_bot_app.core.config import settings
from telegram_bot_app.db.base import async_session
from telegram_bot_app.models.appointment import Appointment, AppointmentStatusEnum


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


async def _send_confirmation_async(appointment_id: int):
    """Асинхронная отправка подтверждения"""
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
                print(f"Appointment {appointment_id} not found or no client")
                return

            # Форматирование даты
            months = {
                1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
            }
            formatted_date = f"{appointment.date.day} {months[appointment.date.month]}"

            message = (
                f"✅ *Запись подтверждена!*\n\n"
                f"📋 Номер записи: #{appointment.id}\n"
                f"🏛️ Салон: {appointment.salon.name}\n"
                f"💅 Услуга: {appointment.service.name}\n"
                f"👨‍💼 Мастер: {appointment.master.user.full_name}\n"
                f"📅 Дата: {formatted_date}\n"
                f"🕐 Время: {appointment.time_start.strftime('%H:%M')}\n"
                f"💰 Стоимость: {appointment.service.price} тг.\n\n"
                f"Ждем вас! За день до записи придет напоминание 🔔"
            )

            await bot.send_message(
                chat_id=appointment.client.telegram_id,
                text=message
            )
            print(f"✅ Confirmation sent for appointment #{appointment_id}")

    except Exception as e:
        print(f"❌ Error sending confirmation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


@celery_app.task(name="telegram_bot_app.celery_app.tasks.send_appointment_reminders")
def send_appointment_reminders(hours_before: int = None, minutes_before: int = None):
    """
    Отправка напоминаний о предстоящих записях

    Args:
        hours_before: за сколько часов до записи отправлять (24 или 1)
        minutes_before: за сколько минут до записи отправлять (для тестов)
    """
    return run_async(_send_reminders_async(hours_before, minutes_before))


async def _send_reminders_async(minutes_before: int = None, hours_before: int = None):
    bot = Bot(token=settings.BOT_TOKEN)

    try:
        now = datetime.now()

        lead_time = timedelta()
        if minutes_before:
            lead_time = timedelta(minutes=minutes_before)
        elif hours_before:
            lead_time = timedelta(hours=hours_before)
        else:
            return  # ничего не указано

        async with async_session() as db:
            result = await db.execute(
                select(Appointment)
                .where(Appointment.status == AppointmentStatusEnum.BOOKED)
            )
            appointments = result.scalars().all()

            for apt in appointments:
                if not apt.client:
                    continue

                # datetime записи
                appointment_datetime = datetime.combine(apt.date, apt.time_start)

                # если осталось ровно нужное время до записи
                if 0 <= (appointment_datetime - now) <= lead_time:
                    # формируем сообщение
                    message = f"⏰ Напоминание о записи через {minutes_before or hours_before} минут!"
                    await bot.send_message(chat_id=apt.client.telegram_id, text=message)
                    print(f"✅ Reminder sent for appointment #{apt.id}")

    finally:
        await bot.session.close()



@celery_app.task(name="telegram_bot_app.celery_app.tasks.send_cancellation_notification")
def send_cancellation_notification(appointment_id: int, client_telegram_id: int):
    """
    Уведомление об отмене записи
    """
    return run_async(_send_cancellation_async(appointment_id, client_telegram_id))


async def _send_cancellation_async(appointment_id: int, client_telegram_id: int):
    """Асинхронная отправка уведомления об отмене"""
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
        print(f"✅ Cancellation notification sent for appointment #{appointment_id}")

    except Exception as e:
        print(f"❌ Error sending cancellation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()