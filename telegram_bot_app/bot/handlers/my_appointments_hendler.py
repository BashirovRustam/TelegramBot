from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram_bot_app.bot.constants import ReplyButtons
from telegram_bot_app.services.appointment_service import AppointmentService
from telegram_bot_app.services.user_service import UserService
from telegram_bot_app.db.base import async_session
import logging

router = Router()
logger = logging.getLogger(__name__)


# =========================
# handler: Мои записи
# =========================
@router.message(F.text == ReplyButtons.MY_BOOKINGS)
async def my_appointments_handler(message: Message):
    """Обработчик кнопки '📋 Мои записи'"""
    logger.info("Пользователь %d запросил свои записи", message.from_user.id)

    async with async_session() as db:
        user_service = UserService(db)
        user = await user_service.get_by_telegram_id(message.from_user.id)

        if not user:
            logger.warning("Пользователь не найден: telegram_id=%d", message.from_user.id)
            await message.answer("😔 Пользователь не найден. Пожалуйста, используйте команду /start")
            return

        appointment_service = AppointmentService(db)
        appointments = await appointment_service.appointment_crud.get_active_by_client(user.id)

        if not appointments:
            logger.debug("У пользователя user_id=%d нет активных записей", user.id)
            await message.answer(
                "📋 *Мои записи*\n\n"
                "У вас пока нет активных записей.\n"
                "Хотите создать новую запись? Нажмите '➕ Создать запись'",
                parse_mode="Markdown"
            )
            return

        logger.info("Найдено активных записей: %d для user_id=%d", len(appointments), user.id)

        # Отправляем заголовок
        await message.answer("📋 *Мои записи*\n\n", parse_mode="Markdown")

        # Отправляем каждую запись отдельным сообщением с кнопкой
        for apt in appointments:
            apt_with_rel = await appointment_service.appointment_crud.get_with_relations(apt.id)
            if not apt_with_rel:
                continue

            salon = apt_with_rel.salon
            master = apt_with_rel.master
            service = apt_with_rel.service

            date_str = apt.date.strftime("%d.%m.%Y")
            time_start_str = apt.time_start.strftime("%H:%M")
            time_end_str = apt.time_end.strftime("%H:%M")
            status_emoji = "✅" if apt.status.value == "BOOKED" else "❌"
            master_name = master.user.full_name if master and master.user else "Не указан"

            text = (
                f"{status_emoji} *Запись #{apt.id}*\n"
                f"📅 {date_str} с {time_start_str} до {time_end_str}\n"
                f"💇 Услуга: {service.name if service else 'Не указана'}\n"
                f"👨‍💼 Мастер: {master_name}\n"
                f"🏛️ Салон: {salon.name if salon else 'Не указан'}\n"
                f"💰 Цена: {service.price if service else 'Не указана'} тг"
            )

            # Создаем клавиатуру только для этой записи
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"❌ Отменить запись #{apt.id}",
                    callback_data=f"cancel_appointment:{apt.id}"
                )
            ]])

            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# =========================
# callback: Отмена записи
# =========================
@router.callback_query(F.data.startswith("cancel_appointment:"))
async def cancel_appointment_callback(callback: CallbackQuery):
    """Обработчик нажатия на кнопку отмены записи"""
    try:
        appointment_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError) as e:
        logger.error("Неверный формат callback_data: %s от user=%d", callback.data, callback.from_user.id)
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return

    logger.info("Попытка отмены записи: appointment_id=%d, user_telegram_id=%d",
                appointment_id, callback.from_user.id)

    async with async_session() as db:
        user_service = UserService(db)
        user = await user_service.get_by_telegram_id(callback.from_user.id)

        if not user:
            logger.warning("Пользователь не найден при отмене записи: telegram_id=%d", callback.from_user.id)
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        appointment_service = AppointmentService(db)
        success = await appointment_service.cancel_appointment(appointment_id, user.id)

        if success:
            logger.info("✅ Запись отменена: appointment_id=%d, user_id=%d", appointment_id, user.id)
            await callback.answer(f"✅ Запись #{appointment_id} отменена", show_alert=True)

            # 🔔 ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ОБ ОТМЕНЕ
            from telegram_bot_app.celery_app.tasks import _send_cancellation_async
            await _send_cancellation_async(appointment_id, user.telegram_id, callback.bot)

            # Обновляем сообщение
            await callback.message.edit_text(
                callback.message.text + f"\n\n~~❌ Запись #{appointment_id} отменена~~",
                parse_mode="Markdown"
            )
        else:
            logger.warning("Не удалось отменить запись: appointment_id=%d, user_id=%d", appointment_id, user.id)
            await callback.answer(
                "❌ Не удалось отменить запись. Возможно, она уже отменена или не принадлежит вам.",
                show_alert=True
            )
