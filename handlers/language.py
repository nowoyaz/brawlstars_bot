from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import update_user_language, ensure_user_exists
from keyboards.inline_keyboard import language_keyboard, inline_main_menu_keyboard
from utils.helpers import get_user_language

async def cmd_language(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Текст можно вынести в JSON, если нужно. Здесь для примера:
    text = "🌐 Выберите язык:"  # или locale["language_text"] если такой ключ добавите в JSON
    kb = language_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)

async def set_language(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 2:
        lang = data[1]  # "ru" или "eng"
        update_user_language(callback.from_user.id, lang)
        # Обновляем запись пользователя, если необходимо:
        ensure_user_exists(callback.from_user.id, callback.from_user.username or callback.from_user.full_name)
        await callback.message.edit_text(f"Язык переключен на {lang.upper()}!", reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_language(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_language(call, locale), lambda c: c.data == "language")
    dp.register_callback_query_handler(lambda call: set_language(call, locale), lambda c: c.data.startswith("set_language:"))
