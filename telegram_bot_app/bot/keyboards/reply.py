from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telegram_bot_app.bot.constants import ReplyButtons

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=ReplyButtons.CREATE_BOOKING)],
        [KeyboardButton(text=ReplyButtons.MY_BOOKINGS)],
        [KeyboardButton(text=ReplyButtons.AUTHOR)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)
