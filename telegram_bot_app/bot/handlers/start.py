from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from telegram_bot_app.bot.keyboards.reply import main_menu

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    text = (
        "👋 Привет!\n\n"
        "Я — *Staly Bot* 🤖 (но пока еще в тестовом режиме)\n"
        "Помогаю оформить онлайн-запись в салон красоты.\n\n"
        "📌 *Что я умею:*\n"
        "• создавать онлайн-запись\n"
        "• помогать выбрать салон\n"
        "• подбирать услугу и мастера\n\n"
        "🚀 *Как начать работу:*\n"
        "Используй кнопки под полем ввода ⬇️"
    )

    await message.answer(text, reply_markup=main_menu)
