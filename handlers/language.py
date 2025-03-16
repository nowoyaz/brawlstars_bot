from aiogram import types
from aiogram.dispatcher import FSMContext
from utils.helpers import update_user_language, ensure_user_exists, get_user_language
from keyboards.language import get_language_keyboard
from handlers.start import cmd_start

async def cmd_language(message: types.Message):
    """Команда для смены языка"""
    ensure_user_exists(message.from_user.id, message.from_user.username)
    await message.answer("Choose language / Выберите язык", reply_markup=get_language_keyboard())

async def show_language_menu(callback: types.CallbackQuery):
    """Показывает меню выбора языка при нажатии на кнопку в меню"""
    await callback.answer()
    ensure_user_exists(callback.from_user.id, callback.from_user.username)
    await callback.message.edit_text(
        "Choose language / Выберите язык",
        reply_markup=get_language_keyboard()
    )

async def set_language(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора языка"""
    await callback.answer()
    lang = callback.data.split('_')[1]  # lang_ru -> ru или lang_en -> en
    
    if update_user_language(callback.from_user.id, lang):
        # Получаем локализацию на новом языке
        locale = get_user_language(callback.from_user.id)
        await callback.message.edit_text(
            locale.get('language_changed', 'Language changed successfully / Язык успешно изменен')
        )
        # Вызываем команду /start для обновления меню
        await cmd_start(callback.message)
    else:
        await callback.message.edit_text(
            "Error changing language / Ошибка при смене языка"
        )

def register_handlers_language(dp):
    """Регистрация обработчиков языка"""
    dp.register_message_handler(cmd_language, commands="language")
    dp.register_callback_query_handler(show_language_menu, lambda c: c.data == "language")
    dp.register_callback_query_handler(set_language, lambda c: c.data.startswith('lang_'))
