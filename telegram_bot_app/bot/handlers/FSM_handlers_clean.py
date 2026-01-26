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
from telegram_bot_app.services.master_availability_service import MasterAvailabilityService
from telegram_bot_app.services.appointment_service import AppointmentService
from telegram_bot_app.services.user_service import UserService
from telegram_bot_app.db.base import async_session

router = Router()


# ================================
# Шаг 1. Начало записи — выбор салона
# ================================
@router.message(F.text == ReplyButtons.CREATE_BOOKING)
async def start_booking(message: Message, state: FSMContext):
    async with async_session() as db:
        salon_service = SalonService(db)
        salons = await salon_service.salon_crud.get_active()

    if not salons:
        await message.answer("😔 Сейчас нет доступных салонов для записи.")
        return

    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for index, salon in enumerate(salons, start=1):
        # Ограничиваем длину названия салона для кнопки
        salon_name = salon.name
        if len(salon_name) > 30:
            salon_name = salon_name[:27] + "..."
        
        row.append(
            InlineKeyboardButton(
                text=f"🏛️ {salon_name}",
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
        salon_service = SalonService(db)
        salon = await salon_service.get_by_id(salon_id)

    if not salon:
        await callback.answer("❌ Салон не найден", show_alert=True)
        return

    await state.update_data(salon_id=salon_id, salon_name=salon.name)

    salon_name = salon.name if salon else "выбран"

    await callback.message.edit_text(
        f"✅ Салон выбран: {salon_name}\n\n"
        f"🔄 Теперь выберите услугу."
    )

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

    data = await state.get_data()
    salon_id = data.get("salon_id")
    salon_name = data.get("salon_name")

    async with async_session() as db:
        salon_service = SalonService(db)
        service = await salon_service.service_crud.get(service_id)

        if not service:
            await callback.answer("❌ Услуга не найдена", show_alert=True)
            return

        await state.update_data(service_id=service.id, service_name=service.name)
        await state.set_state(BookingStates.waiting_for_master)

    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга выбрана: {service.name}\n\n"
        f"🔄 Теперь выберите мастера..."
    )

    await show_masters(callback.message, state)

    await callback.answer()


# ================================
# Шаг 4. Выбор даты
# ================================
@router.callback_query(
    BookingStates.waiting_for_date,
    F.data.startswith("select_date:")
)
async def date_selected(callback: CallbackQuery, state: FSMContext):
    selected_date_str = callback.data.split(":")[1]

    data = await state.get_data()

    salon_name = data.get("salon_name")
    service_name = data.get("service_name")
    master_name = data.get("master_name")

    from datetime import datetime
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

    formatted_date = f"{selected_date.day} {months[selected_date.month]} ({weekdays[selected_date.weekday()]})"

    await state.update_data(selected_date=selected_date_str)

    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга: {service_name}\n"
        f"✅ Мастер: {master_name}\n"
        f"✅ Дата: {formatted_date}\n\n"
        f"🔄 Теперь выберите время..."
    )

    await state.set_state(BookingStates.waiting_for_time)
    await show_available_times(callback.message, state)
    await callback.answer()


# ================================
# Шаг 5. Выбор времени
# ================================
@router.callback_query(
    BookingStates.waiting_for_time,
    F.data.startswith("select_time:")
)
async def time_selected(callback: CallbackQuery, state: FSMContext):
    selected_time_str = callback.data.split("select_time:")[1]

    data = await state.get_data()

    salon_name = data.get("salon_name")
    service_name = data.get("service_name")
    master_name = data.get("master_name")
    selected_date = data.get("selected_date")

    if ":" in selected_time_str:
        hour, minute = map(int, selected_time_str.split(":"))
        formatted_time = f"{hour:02d}:{minute:02d}"
    else:
        formatted_time = selected_time_str

    from datetime import datetime
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    formatted_date = f"{date_obj.day} {months[date_obj.month]} ({weekdays[date_obj.weekday()]})"

    await state.update_data(selected_time=selected_time_str)

    await callback.message.edit_text(
        f"✅ Салон: {salon_name}\n"
        f"✅ Услуга: {service_name}\n"
        f"✅ Мастер: {master_name}\n"
        f"✅ Дата: {formatted_date}\n"
        f"✅ Время: {formatted_time}\n\n"
        f"🔄 Подтвердите запись..."
    )

    await state.set_state(BookingStates.waiting_for_confirmation)
    await show_confirmation_keyboard(callback.message, state)
    await callback.answer()


# ================================
# Шаг 6. Подтверждение записи
# ================================
@router.callback_query(
    BookingStates.waiting_for_confirmation,
    F.data.startswith("confirm_booking:")
)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "confirm":
        await create_appointment_record(callback, state)
    elif action == "cancel":
        await callback.message.edit_text(
            "❌ Запись отменена\n\n"
            "Вы можете начать новую запись, нажав кнопку '➕ Создать запись'"
        )
        await state.clear()

    await callback.answer()


async def create_appointment_record(callback: CallbackQuery, state: FSMContext):
    """Создание записи в БД"""
    data = await state.get_data()

    print(f"DEBUG FSM: State data = {data}")

    salon_id = data.get("salon_id")
    service_id = data.get("service_id")
    master_id = data.get("master_id")
    selected_date = data.get("selected_date")
    selected_time = data.get("selected_time")

    print(
        f"DEBUG FSM: Extracted data - salon_id={salon_id}, service_id={service_id}, master_id={master_id}, date={selected_date}, time={selected_time}")

    telegram_id = callback.from_user.id
    client_name = callback.from_user.full_name or f"User_{telegram_id}"

    print(f"DEBUG FSM: Telegram ID = {telegram_id}")

    if not all([salon_id, service_id, master_id, selected_date, selected_time]):
        await callback.message.edit_text(
            "❌ Ошибка: не все данные для записи доступны. Попробуйте начать заново."
        )
        await state.clear()
        return

    async with async_session() as db:
        # Создаем/получаем пользователя
        user_service = UserService(db)
        user = await user_service.get_or_create_user(
            telegram_id=telegram_id,
            full_name=client_name
        )

        print(f"DEBUG FSM: User created/found - id={user.id}, telegram_id={user.telegram_id}")

        # Создаем запись используя user.id (а не telegram_id)
        appointment_service = AppointmentService(db)
        result = await appointment_service.create_appointment(
            client_id=user.id,  # ВАЖНО: используем user.id
            salon_id=salon_id,
            master_id=master_id,
            service_id=service_id,
            appointment_date=selected_date,
            appointment_time=selected_time
        )

        # Коммитим все изменения
        await db.commit()

    if result:
        # 🔔 ОТПРАВЛЯЕМ ПОДТВЕРЖДЕНИЕ НАПРЯМУЮ (без Celery)
        from telegram_bot_app.celery_app.tasks import _send_confirmation_async
        await _send_confirmation_async(result['id'])

        from datetime import datetime
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

        formatted_date = f"{date_obj.day} {months[date_obj.month]} ({weekdays[date_obj.weekday()]})"

        await callback.message.edit_text(
            f"✅ **Запись успешно создана!**\n\n"
            f"📋 Номер записи: #{result['id']}\n"
            f"🏛️ Салон: {data.get('salon_name', 'Не указан')}\n"
            f"✨ Услуга: {result['service_name']}\n"
            f"👨‍💼 Мастер: {data.get('master_name', 'Не указан')}\n"
            f"📅 Дата: {formatted_date}\n"
            f"🕐 Время: {selected_time}\n"
            f"💰 Цена: {result['service_price']} тг.\n"
            f"⏱️ Длительность: {result['service_duration']} минут\n\n"
            f"📝 Приходите за 5 минут до начала записи\n"
            f"📱 Для отмены записи используйте кнопку '📋 Мои записи'\n"
            f"🔔 Вам придет напоминание за 1 час до визита"
        )
    else:
        await callback.message.edit_text(
            "❌ **Ошибка создания записи**\n\n"
            "К сожалению, не удалось создать запись. Возможно, выбранное время уже занято.\n\n"
            "Попробуйте выбрать другое время или начать заново."
        )

    await state.clear()


async def show_confirmation_keyboard(message: Message, state: FSMContext):
    """Показать клавиатуру подтверждения записи"""
    data = await state.get_data()

    salon_name = data.get("salon_name", "Не указан")
    service_name = data.get("service_name", "Не указана")
    master_name = data.get("master_name", "Не указан")
    selected_date = data.get("selected_date", "Не указана")
    selected_time = data.get("selected_time", "Не указано")

    from datetime import datetime
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    formatted_date = f"{date_obj.day} {months[date_obj.month]} ({weekdays[date_obj.weekday()]})"

    async with async_session() as db:
        salon_service = SalonService(db)
        service = await salon_service.service_crud.get(data.get("service_id"))
        price = service.price if service else "Не указана"

    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking:confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_booking:cancel")
        ]
    ]

    await message.edit_text(
        f"📋 **Подтвердите запись:**\n\n"
        f"🏛️ Салон: {salon_name}\n"
        f"✨ Услуга: {service_name}\n"
        f"👨‍💼 Мастер: {master_name}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {selected_time}\n"
        f"💰 Цена: {price} тг.\n\n"
        f"Все верно? Подтвердите запись:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.message(BookingStates.waiting_for_time, F.text != ReplyButtons.MY_BOOKINGS)
async def show_available_times_handler(message: Message, state: FSMContext):
    await show_available_times(message, state)


async def show_available_times(message: Message, state: FSMContext):
    """Показать доступные временные слоты для записи"""
    data = await state.get_data()
    master_id = data.get("master_id")
    service_id = data.get("service_id")
    selected_date = data.get("selected_date")

    if not master_id or not service_id or not selected_date:
        await message.answer("❌ Сначала выберите мастера, услугу и дату")
        return

    async with async_session() as db:
        salon_service = SalonService(db)
        service = await salon_service.service_crud.get(service_id)

        if not service:
            await message.answer("❌ Услуга не найдена")
            return

        from datetime import datetime
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

        availability_service = MasterAvailabilityService(db)
        available_slots = await availability_service.get_available_time_slots(
            master_id=master_id,
            selected_date=date_obj,
            service_duration_minutes=service.duration_minutes
        )

    if not available_slots:
        await message.answer(
            "😔 К сожалению, нет доступного времени для записи в эту дату.\n\n"
            "Выберите другую дату или попробуйте позже."
        )
        return

    keyboard = []
    row = []

    for i, slot in enumerate(available_slots, start=1):
        time_str = f"{slot.hour:02d}:{slot.minute:02d}"

        row.append(
            InlineKeyboardButton(
                text=f"🕐 {time_str}",
                callback_data=f"select_time:{time_str}"
            )
        )

        if i % 3 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_date")])

    await message.answer(
        "🕐 **Выберите время записи:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.message(BookingStates.waiting_for_date, F.text != ReplyButtons.MY_BOOKINGS)
async def show_available_dates_handler(message: Message, state: FSMContext):
    await show_available_dates(message, state)


async def show_available_dates(message: Message, state: FSMContext):
    """Показать доступные даты для записи"""
    data = await state.get_data()
    master_id = data.get("master_id")
    service_id = data.get("service_id")

    if not master_id or not service_id:
        await message.answer("❌ Сначала выберите мастера и услугу")
        return

    async with async_session() as db:
        salon_service = SalonService(db)
        service = await salon_service.service_crud.get(service_id)

        if not service:
            await message.answer("❌ Услуга не найдена")
            return

        availability_service = MasterAvailabilityService(db)
        available_dates = await availability_service.get_available_dates(
            master_id=master_id,
            service_duration_minutes=service.duration_minutes,
            days_ahead=14
        )

    if not available_dates:
        await message.answer(
            "😔 К сожалению, нет доступных дат для записи к этому мастеру "
            "в ближайшие 14 дней.\n\n"
            "Попробуйте выбрать другого мастера или вернуться позже."
        )
        return

    keyboard = []
    row = []

    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

    for i, available_date in enumerate(available_dates, start=1):
        formatted_date = f"📅 {available_date.day} {months[available_date.month]} ({weekdays[available_date.weekday()]})"

        row.append(
            InlineKeyboardButton(
                text=formatted_date,
                callback_data=f"select_date:{available_date.strftime('%Y-%m-%d')}"
            )
        )

        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_master")])

    await message.answer(
        "📅 **Выберите дату записи:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


async def show_services_for_salon(message: Message, state: FSMContext, salon_id: int):
    async with async_session() as db:
        salon_service = SalonService(db)
        services = await salon_service.get_services_by_salon(salon_id)

        if not services:
            await message.answer("😔 К сожалению, в этом салоне нет доступных услуг.")
            return

        keyboard = []

        for service in services:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"✨ {service.name} ({service.duration_minutes}мин) - {service.price} тг.",
                    callback_data=f"service:{service.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_salon")])

        await message.answer(
            "✨ **Выберите услугу:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )


@router.callback_query(
    BookingStates.waiting_for_master,
    F.data.startswith("master:")
)
async def master_selected(callback: CallbackQuery, state: FSMContext):
    master_id = int(callback.data.split(":")[1])

    data = await state.get_data()
    salon_name = data.get("salon_name")
    service_name = data.get("service_name")

    async with async_session() as db:
        salon_service = SalonService(db)
        master = await salon_service.master_crud.get(master_id)

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

    await show_available_dates(callback.message, state)
    await callback.answer()


@router.message(BookingStates.waiting_for_master, F.text != ReplyButtons.MY_BOOKINGS)
async def show_masters(message: Message, state: FSMContext):
    data = await state.get_data()
    salon_id = data.get("salon_id")
    service_id = data.get("service_id")

    if not salon_id or not service_id:
        await message.answer("❌ Сначала выберите салон и услугу")
        return

    async with async_session() as db:
        salon_service = SalonService(db)
        masters = await salon_service.get_masters_by_service(salon_id, service_id)

        if not masters:
            await message.answer("😔 К сожалению, для этой услуги пока нет доступных мастеров в салоне.")
            return

        keyboard = []
        row = []

        for i, master in enumerate(masters, start=1):
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

        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:to_service")])

        await message.answer(
            "👨‍💼 **Выберите мастера:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )


@router.callback_query(F.data.startswith("back:"))
async def back_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "to_salon":
        await state.set_state(BookingStates.waiting_for_salon)

        async with async_session() as db:
            salon_service = SalonService(db)
            salons = await salon_service.salon_crud.get_active()

        if not salons:
            await callback.message.edit_text("😔 Сейчас нет доступных салонов для записи.")
            return

        keyboard: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []

        for index, salon in enumerate(salons, start=1):
            # Ограничиваем длину названия салона для кнопки
            salon_name = salon.name
            if len(salon_name) > 30:
                salon_name = salon_name[:27] + "..."
            
            row.append(
                InlineKeyboardButton(
                    text=f"🏛️ {salon_name}",
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

    elif action == "to_master":
        await state.set_state(BookingStates.waiting_for_master)

        data = await state.get_data()
        salon_id = data.get("salon_id")
        service_id = data.get("service_id")

        if salon_id and service_id:
            await show_masters(callback.message, state)

    elif action == "to_date":
        await state.set_state(BookingStates.waiting_for_date)
        await show_available_dates(callback.message, state)

    elif action == "to_service":
        await state.set_state(BookingStates.waiting_for_service)

        data = await state.get_data()
        salon_id = data.get("salon_id")

        if salon_id:
            await show_services_for_salon(callback.message, state, salon_id)

    await callback.answer()