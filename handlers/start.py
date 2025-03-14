from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline_keyboard import start_keyboard, inline_main_menu_keyboard
from utils.helpers import ensure_user_exists, process_referral, check_channel_subscription, load_locale, get_user_language
from config import CHANNEL_ID
import re
from database.crud import create_new_user, get_user_by_tg_id, is_user_banned
from utils.helpers import check_referral_achievements

async def cmd_start(message: types.Message, locale, state: FSMContext):
    """
    Обработчик команды /start
    Проверяет наличие пользователя в базе, если его нет - создает
    """
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, заблокирован ли пользователь
    if is_user_banned(message.from_user.id):
        await message.answer("Вы заблокированы в боте.")
        return
    
    # Проверяем, существует ли пользователь в базе
    user = get_user_by_tg_id(message.from_user.id)
    
    # Если пользователя нет в базе, создаем нового
    if not user:
        # Проверяем наличие реферальной ссылки
        args = message.get_args()
        referrer_id = None
        
        # Если есть аргументы, пробуем найти ID реферера
        if args:
            try:
                # Пытаемся преобразовать аргумент в целое число
                referrer_id = int(args)
            except ValueError:
                # Если не получается, ничего не делаем
                pass
                
        # Создаем нового пользователя
        user = create_new_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referrer_id=referrer_id
        )
        
        # Проверяем достижения реферера, если он был указан
        if referrer_id:
            check_referral_achievements(referrer_id)
    
    # Завершаем все FSM-состояния
    await state.finish()
    text = user_locale["start_text"]
    await message.answer(text, reply_markup=start_keyboard(user_locale))


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
