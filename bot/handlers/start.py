from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    text = (
        "👋 Привет!\n\n"
        "Я — *Task Dispatcher Bot* 🤖\n"
        "Помогаю управлять задачами и контролировать их выполнение.\n\n"
        "📌 *Что я умею:*\n"
        "• создавать задачи\n"
        "• назначать исполнителей\n"
        "• отслеживать статусы выполнения\n"
        "• хранить историю изменений задач\n"
        "• работать с вложениями (файлы, документы)\n\n"
        "🚀 *Как начать работу:*\n"
        "Используй кнопки под полем ввода или команды бота.\n"
        "Начни с создания новой задачи."
    )

    await message.answer(
        text=text,
        parse_mode="Markdown",
    )
