from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram_bot_app.bot.constants import BookingStates, ReplyButtons
from telegram_bot_app.services.salon_service import SalonService
from telegram_bot_app.db.base import async_session

router = Router()


# Шаг 1: Начало
@router.message(F.text == ReplyButtons.CREATE_BOOKING)
async def start_booking(message: Message, state: FSMContext):
    async with async_session() as db:
        salon_service = SalonService(db)
        active_salons = await salon_service.get_active_salon_names()
        
        if not active_salons:
            await message.answer("😔 К сожалению, сейчас нет доступных салонов для записи.")
            return
        
        # Создаем inline клавиатуру с плитками салонов (2-3 колонки)
        keyboard = []
        row = []
        
        for i, salon_name in enumerate(active_salons):
            row.append(InlineKeyboardButton(text=f"🏛️ {salon_name}", callback_data=f"salon_{salon_name}"))
            
            # Добавляем новую строку каждые 2 кнопки для формата плитки
            if (i + 1) % 2 == 0 or i == len(active_salons) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer("🏛️ **Выберите салон:**", reply_markup=reply_markup)
        await state.set_state(BookingStates.waiting_for_salon)


# Обработчик выбора салона (inline кнопки)
@router.callback_query(F.data.startswith("salon_"))
async def salon_selected(callback: CallbackQuery, state: FSMContext):
    salon_name = callback.data.replace("salon_", "")
    
    # Сохраняем выбранный салон в состоянии
    await state.update_data(selected_salon=salon_name)
    
    # Подтверждаем выбор
    await callback.message.edit_text(
        f"✅ **Выбран салон:** {salon_name}\n\n"
        f"🔄 Теперь выберите услугу...",
        parse_mode="Markdown"
    )
    
    # Здесь будет логика перехода к выбору услуги
    # await state.set_state(BookingStates.waiting_for_service)
    
    await callback.answer()
