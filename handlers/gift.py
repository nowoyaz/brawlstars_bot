import random
import datetime
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import inline_main_menu_keyboard, gift_keyboard
from utils.helpers import get_user_language, check_channel_subscription, is_user_premium, check_all_sponsor_subscriptions, record_section_visit, check_gift_achievement
from database.crud import get_sponsors, check_user_subscription, get_user_by_id, update_user_last_gift, add_user_crystals, add_coins_to_user

async def cmd_gift(callback: types.CallbackQuery, locale):
    """Обработчик для кнопки 'Подарок'"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "gift")
    
    text = locale["gift_text"]
    kb = gift_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)

async def process_receive_gift(callback: types.CallbackQuery, locale):
    """Обработчик для получения подарка"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    session = SessionLocal()
    user = session.query(User).filter(User.tg_id == callback.from_user.id).first()
    
    # Проверяем подписку на спонсоров или наличие премиум-статуса
    is_premium = is_user_premium(callback.from_user.id)
    has_all_subscriptions = check_all_sponsor_subscriptions(callback.from_user.id)
    
    if not is_premium and not has_all_subscriptions:
        # Получаем список активных спонсоров
        sponsors = get_sponsors(is_active_only=True)
        if sponsors:
            # Создаем клавиатуру со списком спонсоров
            kb = types.InlineKeyboardMarkup(row_width=1)
            for sponsor in sponsors:
                if not check_user_subscription(callback.from_user.id, sponsor.id):
                    kb.add(types.InlineKeyboardButton(
                        text=f"👉 Подписаться на {sponsor.name}",
                        url=sponsor.link
                    ))
            kb.add(types.InlineKeyboardButton(
                text=locale.get("check_subscriptions", "🔄 Проверить подписки"),
                callback_data="receive_gift"
            ))
            kb.add(types.InlineKeyboardButton(
                text=locale.get("back_to_menu", "◀️ В меню"),
                callback_data="back_to_main"
            ))
            
            text = locale["gift_sponsors_required"]
            await callback.message.edit_text(text, reply_markup=kb)
            session.close()
            return
    
    # Проверяем, получал ли пользователь подарок сегодня
    today = datetime.datetime.now().date()
    if user.last_gift and user.last_gift.date() == today:
        text = locale["gift_time_error"]
        await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))
        session.close()
        return
    
    # Генерируем случайное количество монет
    amount = random.randint(10, 50)
    
    # Обновляем время последнего подарка и баланс монет
    update_user_last_gift(callback.from_user.id)
    add_coins_to_user(callback.from_user.id, amount)
    
    # Выдаем достижение "Испытать удачу"
    check_gift_achievement(callback.from_user.id)
    
    text = locale["gift_success"].format(amount=amount)
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))
    session.close()

async def process_gift_back(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_gift(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_gift(call, locale), lambda c: c.data == "gift")
    dp.register_callback_query_handler(lambda call: process_receive_gift(call, locale), lambda c: c.data == "receive_gift")
    dp.register_callback_query_handler(lambda call: process_gift_back(call, locale), lambda c: c.data == "back_to_main")
