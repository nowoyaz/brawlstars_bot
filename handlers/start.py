from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline_keyboard import start_keyboard, inline_main_menu_keyboard
from utils.helpers import ensure_user_exists, process_referral  # ensure_user_exists – функция создания пользователя, если его нет
from utils.helpers import get_user_language
from config import CHANNEL_ID

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


async def check_subscription_callback(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Проверяем подписку на канал
    try:
        user_id = callback.from_user.id
        member = await callback.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        # Если пользователь подписан на канал
        if member.status not in ["left", "kicked", "banned"]:
            text = locale["menu_text"]
            await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))
        else:
            # Пользователь не подписан или покинул канал
            text = locale.get("subscription_required", "Для использования бота необходимо подписаться на канал.")
            await callback.message.edit_text(text, reply_markup=start_keyboard(locale))
    except Exception as e:
        # Ошибка при проверке подписки
        text = locale.get("error_checking_subscription", "Произошла ошибка при проверке подписки. Попробуйте позже.")
        await callback.message.edit_text(text, reply_markup=start_keyboard(locale))


def register_handlers_start(dp: Dispatcher, locale):
    dp.register_message_handler(lambda message, state: cmd_start(message, locale, state), commands=["start"])
    dp.register_callback_query_handler(lambda call: process_start_callback(call, locale), lambda c: c.data == "menu")
    dp.register_callback_query_handler(lambda call: check_subscription_callback(call, locale), lambda c: c.data == "check_subscription")
