from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime

from telegram_bot_app.bot.constants import ReplyButtons
from telegram_bot_app.services.appointment_service import AppointmentService
from telegram_bot_app.services.user_service import UserService
from telegram_bot_app.db.base import async_session

router = Router()


@router.message(F.text == ReplyButtons.MY_BOOKINGS)
async def my_appointments_handler(message: Message):
    """Обработчик кнопки '📋 Мои записи'"""
    
    async with async_session() as db:
        # Получаем пользователя по telegram_id
        user_service = UserService(db)
        user = await user_service.get_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer("😔 Пользователь не найден. Пожалуйста, используйте команду /start")
            return
        
        # Получаем активные записи пользователя
        appointment_service = AppointmentService(db)
        appointments = await appointment_service.appointment_crud.get_active_by_client(user.id)
        
        if not appointments:
            await message.answer(
                "📋 *Мои записи*\n\n"
                "У вас пока нет активных записей.\n"
                "Хотите создать новую запись? Нажмите '➕ Создать запись'"
            )
            return
        
        # Формируем сообщение со списком записей
        text = "📋 *Мои записи*\n\n"
        
        for appointment in appointments:
            # Загружаем связанные данные для красивого отображения
            appointment_with_relations = await appointment_service.appointment_crud.get_with_relations(appointment.id)
            
            if appointment_with_relations:
                salon = appointment_with_relations.salon
                master = appointment_with_relations.master
                service = appointment_with_relations.service
                
                # Форматируем дату и время
                date_str = appointment.date.strftime("%d.%m.%Y")
                time_start_str = appointment.time_start.strftime("%H:%M")
                time_end_str = appointment.time_end.strftime("%H:%M")
                
                # Определяем статус записи
                status_emoji = "✅" if appointment.status.value == "BOOKED" else "❌"
                
                # Получаем имя мастера через связанную модель User
                master_name = master.user.full_name if master and master.user else "Не указан"
                
                text += f"{status_emoji} *Запись #{appointment.id}*\n"
                text += f"📅 {date_str} с {time_start_str} до {time_end_str}\n"
                text += f"💇 Услуга: {service.name if service else 'Не указана'}\n"
                text += f"👨‍💼 Мастер: {master_name}\n"
                text += f"🏛️ Салон: {salon.name if salon else 'Не указан'}\n"
                text += f"💰 Цена: {service.price if service else 'Не указана'} тг\n"
                text += "-" * 30 + "\n"
        
        # Создаем inline клавиатуру с кнопками отмены для каждой записи
        keyboard_buttons = []
        for appointment in appointments:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"❌ Отменить запись #{appointment.id}",
                    callback_data=f"cancel_appointment:{appointment.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")


@router.callback_query(F.data.startswith("cancel_appointment:"))
async def cancel_appointment_callback(callback: CallbackQuery):
    """Обработчик нажатия на кнопку отмены записи"""
    
    # Извлекаем ID записи из callback_data
    try:
        appointment_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return
    
    async with async_session() as db:
        # Получаем пользователя по telegram_id
        user_service = UserService(db)
        user = await user_service.get_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Отменяем запись через сервисный слой
        appointment_service = AppointmentService(db)
        success = await appointment_service.cancel_appointment(appointment_id, user.id)
        
        if success:
            await callback.answer(f"✅ Запись #{appointment_id} отменена", show_alert=True)
            
            # Обновляем сообщение, убирая кнопку отмены
            await callback.message.edit_text(
                callback.message.text + f"\n\n~~❌ Запись #{appointment_id} отменена~~",
                parse_mode="Markdown"
            )
        else:
            await callback.answer(
                "❌ Не удалось отменить запись. Возможно, она уже отменена или не принадлежит вам.", 
                show_alert=True
            )