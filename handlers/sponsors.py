from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from database.crud import get_sponsors, check_user_subscription, add_user_subscription, get_user_by_id
from keyboards.inline_keyboard import sponsors_list_keyboard, back_to_menu_keyboard
from utils.helpers import get_user_language, check_channel_subscription
import logging

logger = logging.getLogger(__name__)

async def cmd_sponsors(message: types.Message, locale):
    """Обработчик команды для показа спонсоров"""
    user_locale = get_user_language(message.from_user.id)
    
    # Получаем активных спонсоров
    sponsors = get_sponsors(only_active=True)
    
    # Получаем пользователя для проверки премиум-статуса
    user = get_user_by_id(message.from_user.id)
    
    # Если у пользователя есть премиум, показываем особое сообщение
    if user and user.is_premium:
        text = f"{user_locale['sponsors_title']}\n\n{user_locale['sponsors_premium_description']}"
        await message.answer(text, reply_markup=back_to_menu_keyboard(user_locale))
        return
    
    if not sponsors:
        text = f"{user_locale['sponsors_title']}\n\n{user_locale['no_sponsors']}"
        await message.answer(text, reply_markup=back_to_menu_keyboard(user_locale))
        return
    
    # Получаем подписки пользователя
    user_subscriptions = [
        sub.sponsor_id for sub in check_user_subscription(message.from_user.id)
    ]
    
    text = f"{user_locale['sponsors_title']}\n\n{user_locale['sponsors_description']}"
    
    # Выводим список спонсоров и кнопки
    await message.answer(
        text,
        reply_markup=sponsors_list_keyboard(user_locale, sponsors, message.from_user.id, user_subscriptions)
    )

async def process_check_subscription(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик проверки подписки на спонсора"""
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Получаем спонсора
    sponsors = get_sponsors(only_active=True)
    sponsor = next((s for s in sponsors if s.id == sponsor_id), None)
    
    if not sponsor:
        await callback.answer(user_locale["sponsor_not_found"], show_alert=True)
        return
    
    # Проверяем, подписан ли пользователь
    user_subscriptions = [
        sub.sponsor_id for sub in check_user_subscription(callback.from_user.id)
    ]
    
    if sponsor_id in user_subscriptions:
        await callback.answer(user_locale["already_subscribed"], show_alert=True)
        return
    
    # Отправляем сообщение с информацией о спонсоре
    text = user_locale["check_subscription_text"].format(name=sponsor.name)
    
    # Создаем клавиатуру с кнопкой для перехода по ссылке и кнопками подтверждения/отмены
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопку с прямой ссылкой на канал спонсора
    keyboard.add(types.InlineKeyboardButton(text=f"📣 {sponsor.name}", url=sponsor.link))
    
    # Добавляем кнопку подтверждения подписки
    keyboard.add(types.InlineKeyboardButton(
        text=user_locale["confirm_subscription"],
        callback_data=f"confirm_subscription:{sponsor_id}"
    ))
    
    # Добавляем кнопку возврата к списку спонсоров
    keyboard.add(types.InlineKeyboardButton(
        text=user_locale["back_to_sponsors"],
        callback_data="show_sponsors"
    ))
    
    await callback.message.edit_text(text, reply_markup=keyboard)

async def process_confirm_subscription(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик подтверждения подписки на спонсора"""
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Получаем спонсора
    sponsors = get_sponsors(only_active=True)
    sponsor = next((s for s in sponsors if s.id == sponsor_id), None)
    
    if not sponsor:
        await callback.answer(user_locale["sponsor_not_found"], show_alert=True)
        return
    
    # Проверяем подписку на канал спонсора
    is_subscribed = False
    try:
        # Если у нас есть channel_id, проверяем подписку через Telegram API
        if hasattr(sponsor, 'channel_id') and sponsor.channel_id:
            is_subscribed = await check_channel_subscription(callback.bot, callback.from_user.id, sponsor.channel_id)
        else:
            # Иначе просто доверяем подтверждению пользователя
            is_subscribed = True
        
        if not is_subscribed:
            await callback.answer(user_locale["sponsor_not_subscribed"], show_alert=True)
            return
        
        # Добавляем подписку
        add_user_subscription(callback.from_user.id, sponsor_id)
        
        # Отправляем сообщение об успешной подписке
        text = user_locale["subscription_success"].format(name=sponsor.name)
        
        await callback.message.edit_text(
            text,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    text=user_locale["back_to_sponsors"],
                    callback_data="show_sponsors"
                )
            )
        )
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении подписки: {str(e)}")
        await callback.answer(user_locale["subscription_error"], show_alert=True)

async def process_show_sponsors(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для возврата к списку спонсоров"""
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем активных спонсоров
    sponsors = get_sponsors(only_active=True)
    
    # Получаем пользователя для проверки премиум-статуса
    user = get_user_by_id(callback.from_user.id)
    
    # Если у пользователя есть премиум, показываем особое сообщение
    if user and user.is_premium:
        text = f"{user_locale['sponsors_title']}\n\n{user_locale['sponsors_premium_description']}"
        await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(user_locale))
        return
    
    if not sponsors:
        text = f"{user_locale['sponsors_title']}\n\n{user_locale['no_sponsors']}"
        await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(user_locale))
        return
    
    # Получаем подписки пользователя
    user_subscriptions = [
        sub.sponsor_id for sub in check_user_subscription(callback.from_user.id)
    ]
    
    text = f"{user_locale['sponsors_title']}\n\n{user_locale['sponsors_description']}"
    
    # Выводим список спонсоров и кнопки
    await callback.message.edit_text(
        text,
        reply_markup=sponsors_list_keyboard(user_locale, sponsors, callback.from_user.id, user_subscriptions)
    )

def register_handlers_sponsors(dp: Dispatcher, locale):
    """Регистрация обработчиков для спонсоров"""
    dp.register_message_handler(lambda message: cmd_sponsors(message, locale), commands=["sponsors"])
    dp.register_callback_query_handler(
        lambda c, state: process_check_subscription(c, state, locale),
        lambda c: c.data.startswith("check_subscription:")
    )
    dp.register_callback_query_handler(
        lambda c, state: process_confirm_subscription(c, state, locale),
        lambda c: c.data.startswith("confirm_subscription:")
    )
    dp.register_callback_query_handler(
        lambda c, state: process_show_sponsors(c, state, locale),
        lambda c: c.data == "show_sponsors"
    ) 