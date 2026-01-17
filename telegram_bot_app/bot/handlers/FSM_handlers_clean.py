from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
)
from telegram_bot_app.bot.constants import BookingStates, ReplyButtons
from telegram_bot_app.services.salon_service import SalonService
from telegram_bot_app.db.base import async_session

router = Router()


# ================================
# Шаг 1. Начало записи — выбор салона
# ================================
@router.message(F.text == ReplyButtons.CREATE_BOOKING)
async def start_booking(message: Message, state: FSMContext):
    async with async_session() as db:
        async with db.begin():
            salon_service = SalonService(db)
            salons = await salon_service.salon_crud.get_active()

    if not salons:
        await message.answer("😔 Сейчас нет доступных салонов для записи.")
        return

    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for index, salon in enumerate(salons, start=1):
        row.append(
            InlineKeyboardButton(
                text=f"🏛️ {salon.name}",
                callback_data=f"salon:{salon.id}",
            )
        )

        if index % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await message.answer(
        "🏛️ Выберите салон:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )

    await state.set_state(BookingStates.waiting_for_salon)


# ================================
# Шаг 2. Обработка выбора салона
# ================================
@router.callback_query(
    BookingStates.waiting_for_salon,
    F.data.startswith("salon:")
)
async def salon_selected(callback: CallbackQuery, state: FSMContext):
    salon_id = int(callback.data.split(":")[1])

    async with async_session() as db:
        async with db.begin():
            salon_service = SalonService(db)
            salon = await salon_service.get_by_id(salon_id)

    if not salon:
        await callback.answer("❌ Салон не найден", show_alert=True)
        return

    # Сохраняем ID и имя салона в состоянии
    await state.update_data(salon_id=salon_id, salon_name=salon.name)

    salon_name = salon.name if salon else "выбран"

    await callback.message.edit_text(
        f"✅ Салон выбран: {salon_name}\n\n"
        f"🔄 Теперь выберите услугу."
    )
    
    # Сразу показываем услуги, не ждем сообщения
    await show_services_for_salon(callback.message, state, salon_id)
    
    await state.set_state(BookingStates.waiting_for_service)
    await callback.answer()


# ================================
# Шаг 3. Выбор услуги
# ================================
@router.callback_query(
    BookingStates.waiting_for_service,
    F.data.startswith("service:")
)
async def service_selected(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    salon_id = data.get("salon_id")
    salon_name = data.get("salon_name")
    
    async with async_session() as db:
        async with db.begin():
            salon_service = SalonService(db)
            service = await salon_service.service_crud.get(service_id)
        
        if not service:
            await callback.answer("❌ Услуга не найдена", show_alert=True)
            return
        
        # Сохраняем ID услуги в состоянии
        await state.update_data(service_id=service.id, service_name=service.name)
        
        # Переключаем состояние на выбор мастера
        await state.set_state(BookingStates.waiting_for_master)
    
    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга выбрана: {service.name}\n\n"
        f"🔄 Теперь выберите мастера..."
    )
    
    # Сразу показываем мастеров, не ждем сообщения
    await show_masters(callback.message, state)
    
    await callback.answer()


# ================================
# Шаг 5. Выбор даты
# ================================
@router.callback_query(
    BookingStates.waiting_for_date,
    F.data.startswith("date:")
)
async def date_selected(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split(":")[1]
    
    # Получаем данные из состояния
    data = await state.get_data()
    print(f"DEBUG: Date selected - current state data: {data}")
    
    salon_id = data.get("salon_id")
    salon_name = data.get("salon_name")
    service_name = data.get("service_name")
    master_name = data.get("master_name")
    
    # Сохраняем выбранную дату в состоянии
    await state.update_data(selected_date=selected_date)
    
    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга: {service_name}\n"
        f"✅ Мастер: {master_name}\n"
        f"✅ Дата: {selected_date}\n\n"
        f"🔄 Теперь выберите время..."
    )
    
    # Переключаем состояние на выбор времени
    await state.set_state(BookingStates.waiting_for_time)
    
    await callback.answer()


# Обработчик состояния waiting_for_date - показываем календарь
@router.message(BookingStates.waiting_for_date)
async def show_date_calendar(message: Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    salon_id = data.get("salon_id")
    
    if not salon_id:
        await message.answer("❌ Сначала выберите салон")
        return
    
    # Создаем простой календарь на ближайшие 7 дней
    from datetime import datetime, timedelta
    import calendar
    
    today = datetime.now().date()
    keyboard = []
    
    # Создаем кнопки для дней недели
    for i in range(7):
        date = today + timedelta(days=i)
        day_name = calendar.day_name[date.weekday()]
        
        # Формируем текст кнопки
        button_text = f"{date.day:02d} {day_name}"
        if i == 0:
            button_text = f"📅 Сегодня ({button_text})"
        
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"date:{date.strftime('%Y-%m-%d')}"
        )])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_master")])
    
    await message.answer(
        "📅 **Выберите дату записи:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


# Функция показа услуг салона
async def show_services_for_salon(message: Message, state: FSMContext, salon_id: int):
    async with async_session() as db:
        async with db.begin():
            salon_service = SalonService(db)
            services = await salon_service.get_services_by_salon(salon_id)
        
        if not services:
            await message.answer("😔 К сожалению, в этом салоне нет доступных услуг.")
            return
        
        # Создаем inline клавиатуру с услугами (2 в ряд)
        keyboard = []
        row = []
        
        for i, service in enumerate(services, start=1):
            row.append(
                InlineKeyboardButton(
                    text=f"💅 {service.name} ({service.duration_minutes}мин) - {service.price}₽",
                    callback_data=f"service:{service.id}"
                )
            )
            
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_salon")])
        
        await message.answer(
            "💅 **Выберите услугу:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )


# ================================
# Шаг 4. Выбор мастера
# ================================
@router.callback_query(
    BookingStates.waiting_for_master,
    F.data.startswith("master:")
)
async def master_selected(callback: CallbackQuery, state: FSMContext):
    master_id = int(callback.data.split(":")[1])

    data = await state.get_data()
    salon_id = data.get("salon_id")
    salon_name = data.get("salon_name")
    service_name = data.get("service_name")

    async with async_session() as db:
        salon_service = SalonService(db)
        master = await salon_service.master_crud.get(master_id)  # уже с selectinload(user)

    if not master:
        await callback.answer("❌ Мастер не найден", show_alert=True)
        return

    master_name = master.user.full_name if master.user else f"Мастер {master.id}"

    await state.update_data(master_id=master.id, master_name=master_name)
    await state.set_state(BookingStates.waiting_for_date)

    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга: {service_name}\n"
        f"✅ Мастер: {master_name}\n\n"
        f"🔄 Теперь выберите дату..."
    )

    await callback.answer()


# Обработчик состояния waiting_for_master - показываем мастеров
@router.message(BookingStates.waiting_for_master)
async def show_masters(message: Message, state: FSMContext):
    # Получаем ID салона из состояния
    data = await state.get_data()
    salon_id = data.get("salon_id")
    
    if not salon_id:
        await message.answer("❌ Сначала выберите салон")
        return
    
    async with async_session() as db:
        async with db.begin():
            salon_service = SalonService(db)
            masters = await salon_service.get_master_by_salon(salon_id)
        
        if not masters:
            await message.answer("😔 К сожалению, в этом салоне нет доступных мастеров.")
            return
        
        # Создаем inline клавиатуру с мастерами (2 в ряд)
        keyboard = []
        row = []
        
        for i, master in enumerate(masters, start=1):
            # Используем загруженные данные для доступа к user
            master_name = master.user.full_name if hasattr(master, 'user') and master.user else f"Мастер {master.id}"
            row.append(
                InlineKeyboardButton(
                    text=f"👨‍💼 {master_name}",
                    callback_data=f"master:{master.id}"
                )
            )
            
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_service")])
        
        await message.answer(
            "👨‍💼 **Выберите мастера:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )


# ================================
# Обработчики кнопки "Назад"
# ================================
@router.callback_query(F.data.startswith("back:"))
async def back_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    
    if action == "to_salon":
        # Возврат к выбору салона
        await state.set_state(BookingStates.waiting_for_salon)
        
        async with async_session() as db:
            async with db.begin():
                salon_service = SalonService(db)
                salons = await salon_service.salon_crud.get_active()
        
        if not salons:
            await callback.message.edit_text("😔 Сейчас нет доступных салонов для записи.")
            return
        
        keyboard: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []

        for index, salon in enumerate(salons, start=1):
            row.append(
                InlineKeyboardButton(
                    text=f"🏛️ {salon.name}",
                    callback_data=f"salon:{salon.id}",
                )
            )

            if index % 2 == 0:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)
        
        await callback.message.edit_text(
            "🏛️ Выберите салон:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )
    
    elif action == "to_service":
        # Возврат к выбору услуги
        await state.set_state(BookingStates.waiting_for_service)
        
        data = await state.get_data()
        salon_id = data.get("salon_id")
        
        if salon_id:
            await show_services_for_salon(callback.message, state, salon_id)
    
    await callback.answer()
