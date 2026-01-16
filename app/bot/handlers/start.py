# from aiogram import Router
# from aiogram.filters import CommandStart
# from aiogram.types import Message
#
# router = Router()
#
#
# @router.message(CommandStart())
# async def start_handler(message: Message):
#     text = (
#         "👋 Привет!\n\n"
#         "Я — *Task Dispatcher Bot* 🤖\n"
#         "Помогаю управлять задачами и контролировать их выполнение.\n\n"
#         "📌 *Что я умею:*\n"
#         "• создавать задачи\n"
#         "• назначать исполнителей\n"
#         "• отслеживать статусы выполнения\n"
#         "• хранить историю изменений задач\n"
#         "• работать с вложениями (файлы, документы)\n\n"
#         "🚀 *Как начать работу:*\n"
#         "Используй кнопки под полем ввода или команды бота.\n"
#         "Начни с создания новой задачи."
#     )
#
#     await message.answer(
#         text=text,
#         parse_mode="Markdown",
#     )


from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.helps import reply_menu

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Я — Task Dispatcher Bot 🤖\n\n"
        "⬇️ Используй кнопки внизу",
        reply_markup=reply_menu
    )
