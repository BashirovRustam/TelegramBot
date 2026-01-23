from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from telegram_bot_app.bot.keyboards.reply import main_menu
from telegram_bot_app.bot.constants import ReplyButtons

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


@router.message(F.text == ReplyButtons.AUTHOR)
async def author_handler(message: Message):
    """Обработчик кнопки '👨‍💻 Автор'"""
    await message.answer(
        "👨‍💻 Автор: Rustam Bashirov\n\n"
        "GitHub: https://github.com/BashirovRustam/\n"
        "TG: @ArdSkelige\n"
        "HH: https://almaty.hh.kz/resume/658b73b3ff0fde0cff0039ed1f686837776745?hhtmFrom=resume_list\n\n"
        "📝 О проекте:\n"
        "Проект создан для демонстрации навыков разработки на FastAPI, создания Telegram-ботов, "
        "реализации системы онлайн-записи в салон и интеграции с внешними API.\n\n"
        "🛠️ Используемые технологии:\n"
        "• FastAPI\n"
        "• SQLAlchemy\n"
        "• Pydantic\n"
        "• Redis\n"
        "• Celery\n"
        "• Docker\n"
        "• PostgreSQL\n"
        "• Aiogram\n"
        "• Асинхронное программирование на Python",
        parse_mode=None
    )
