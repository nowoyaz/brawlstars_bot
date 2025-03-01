from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline_keyboard import start_keyboard, inline_main_menu_keyboard
from utils.helpers import ensure_user_exists, process_referral  # ensure_user_exists – функция создания пользователя, если его нет
from utils.helpers import get_user_language

async def cmd_start(message: types.Message, locale, state: FSMContext):
    # Завершаем все FSM-состояния
    locale = get_user_language(message.from_user.id)
    await state.finish()
    # Создаем запись пользователя, если ее еще нет
    ensure_user_exists(message.from_user.id, message.from_user.username or message.from_user.full_name)
    # Если есть аргумент, обрабатываем реферал
    args = message.get_args()  # аргументы после /start
    if args.isdigit():
        inviter_id = int(args)
        process_referral(message.from_user.id, inviter_id)
    text = locale["start_text"]
    await message.answer(text, reply_markup=start_keyboard(locale))


async def process_start_callback(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["menu_text"]
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))


def register_handlers_start(dp: Dispatcher, locale):
    dp.register_message_handler(lambda message, state: cmd_start(message, locale, state), commands=["start"])
    dp.register_callback_query_handler(lambda call: process_start_callback(call, locale), lambda c: c.data == "menu")
