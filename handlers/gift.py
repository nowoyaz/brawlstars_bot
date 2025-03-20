import random
import datetime
import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import inline_main_menu_keyboard, gift_keyboard
from utils.helpers import get_user_language, check_channel_subscription, is_user_premium, check_all_sponsor_subscriptions, record_section_visit, check_gift_achievement
from database.crud import get_sponsors, check_user_subscription, get_user_by_id, update_user_last_gift, add_user_crystals, add_coins_to_user, add_user_subscription

logger = logging.getLogger(__name__)

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
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил подарок")
    
    locale = get_user_language(user_id)
    await callback.answer()
    
    session = SessionLocal()
    user = session.query(User).filter(User.tg_id == user_id).first()
    
    # Проверяем подписку на спонсоров или наличие премиум-статуса
    is_premium = is_user_premium(user_id)
    logger.info(f"Пользователь {user_id} премиум: {is_premium}")
    
    # Получаем список активных спонсоров
    sponsors = get_sponsors(is_active_only=True)
    logger.info(f"Найдено активных спонсоров: {len(sponsors)}")
    
    if not is_premium and sponsors:
        # Проверяем реальные подписки на каналы
        kb = types.InlineKeyboardMarkup(row_width=1)
        has_all_subscriptions = True
        unsubscribed_sponsors = []
        
        for sponsor in sponsors:
            logger.info(f"Проверка подписки пользователя {user_id} на спонсора {sponsor.name} (ID: {sponsor.id})")
            if sponsor.channel_id:
                is_subscribed = await check_channel_subscription(callback.bot, user_id, sponsor.channel_id)
                logger.info(f"Результат проверки подписки на {sponsor.name}: {is_subscribed}")
                
                if is_subscribed:
                    # Если пользователь подписан, добавляем запись в базу
                    add_user_subscription(user_id, sponsor.id)
                    logger.info(f"Добавлена запись о подписке пользователя {user_id} на спонсора {sponsor.name}")
                else:
                    has_all_subscriptions = False
                    unsubscribed_sponsors.append(sponsor)
                    logger.info(f"Пользователь {user_id} не подписан на спонсора {sponsor.name}")
                    kb.add(types.InlineKeyboardButton(
                        text=f"👉 Подписаться на {sponsor.name}",
                        url=sponsor.link
                    ))
        
        if not has_all_subscriptions:
            logger.info(f"Пользователь {user_id} не подписан на всех спонсоров. Неподписанные спонсоры: {[s.name for s in unsubscribed_sponsors]}")
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
        else:
            logger.info(f"Пользователь {user_id} подписан на всех спонсоров")
    
    # Проверяем, получал ли пользователь подарок сегодня
    today = datetime.datetime.now().date()
    if user.last_gift and user.last_gift.date() == today:
        logger.info(f"Пользователь {user_id} уже получал подарок сегодня")
        text = locale["gift_time_error"]
        await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))
        session.close()
        return
    
    # Проверяем подписки еще раз перед выдачей подарка
    if not is_premium and sponsors:
        logger.info(f"Вторичная проверка подписок пользователя {user_id}")
        has_all_subscriptions = True
        for sponsor in sponsors:
            if sponsor.channel_id:
                is_subscribed = await check_channel_subscription(callback.bot, user_id, sponsor.channel_id)
                logger.info(f"Вторичная проверка подписки на {sponsor.name}: {is_subscribed}")
                if not is_subscribed:
                    has_all_subscriptions = False
                    logger.info(f"Пользователь {user_id} не подписан на спонсора {sponsor.name} при вторичной проверке")
                    break
        
        if not has_all_subscriptions:
            logger.info(f"Пользователь {user_id} не прошел вторичную проверку подписок")
            text = locale["gift_sponsors_required"]
            await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))
            session.close()
            return
        else:
            logger.info(f"Пользователь {user_id} прошел вторичную проверку подписок")
    
    # Генерируем случайное количество монет
    amount = random.randint(10, 50)
    logger.info(f"Выдача подарка пользователю {user_id}: {amount} монет")
    
    # Обновляем время последнего подарка и баланс монет
    update_user_last_gift(user_id)
    add_coins_to_user(user_id, amount)
    
    # Выдаем достижение "Испытать удачу"
    check_gift_achievement(user_id)
    
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
