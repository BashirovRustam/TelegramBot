from aiogram import Router
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

router = Router()

# =========================
# REPLY кнопки (внизу)
# =========================

reply_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Создать задачу"),
            KeyboardButton(text="ℹ️ Что умеет бот"),
        ]
    ],
    resize_keyboard=True
)

# =========================
# INLINE кнопки (под сообщением)
# =========================

inline_actions = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data="confirm_action"
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_action"
            ),
        ]
    ]
)

# =========================
# REPLY кнопка → текст
# =========================

@router.message(lambda m: m.text == "➕ Создать задачу")
async def create_task_reply(message: Message):
    await message.answer(
        "Ты нажал **REPLY-кнопку** 👇\n\n"
        "Теперь смотри INLINE-кнопки под этим сообщением.",
        reply_markup=inline_actions
    )

@router.message(lambda m: m.text == "ℹ️ Что умеет бот")
async def help_reply(message: Message):
    await message.answer(
        "📌 Бот умеет:\n"
        "• создавать задачи\n"
        "• назначать исполнителей\n"
        "• отслеживать статусы\n\n"
        "Это была REPLY-кнопка 🙂"
    )

# =========================
# INLINE кнопки → callback
# =========================

@router.callback_query(lambda c: c.data == "confirm_action")
async def confirm_inline(callback: CallbackQuery):
    await callback.answer("Подтверждено ✅")
    await callback.message.answer(
        "INLINE-кнопка:\n"
        "• не отправляет текст\n"
        "• вызывает callback"
    )

@router.callback_query(lambda c: c.data == "cancel_action")
async def cancel_inline(callback: CallbackQuery):
    await callback.answer("Отменено ❌")
    await callback.message.answer(
        "INLINE-действие отменено."
    )
