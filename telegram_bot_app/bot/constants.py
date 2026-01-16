class ReplyButtons:
    CREATE_BOOKING = "➕ Создать запись"
    MY_BOOKINGS = "📋 Мои записи"
    ABOUT_BOT = "ℹ️ О боте"




from aiogram.fsm.state import StatesGroup, State

class BookingStates(StatesGroup):
    waiting_for_salon = State()       # Шаг 1: выбор салона
    waiting_for_service = State()     # Шаг 2: выбор услуги
    waiting_for_master = State()      # Шаг 3: выбор мастера
    waiting_for_date = State()        # Шаг 4: выбор даты
    waiting_for_time = State()        # Шаг 5: выбор времени
    waiting_for_confirmation = State() # Шаг 6: подтверждение
