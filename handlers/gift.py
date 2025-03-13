import random
import datetime
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import inline_main_menu_keyboard, gift_keyboard
from utils.helpers import get_user_language, check_channel_subscription
from database.crud import get_sponsors, check_user_subscription, get_user_by_id

async def cmd_gift(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["gift_text"]
    kb = gift_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)

async def process_receive_gift(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == callback.from_user.id).first()
    now = datetime.datetime.utcnow()
    
    # Проверяем, получал ли пользователь подарок сегодня
    if user.last_gift is not None:
        last_gift_date = user.last_gift.date()
        today = now.date()
        if last_gift_date == today:
            # Если подарок уже получен сегодня, показываем сообщение
            session.close()
            await callback.answer(locale["gift_time_error"], show_alert=True)
            return
    
    # Проверяем, подписан ли пользователь на всех активных спонсоров
    # или имеет премиум-статус
    user_has_premium = user.is_premium if hasattr(user, 'is_premium') else False
    
    if not user_has_premium:
        # Получаем всех активных спонсоров
        sponsors = get_sponsors(only_active=True)
        
        if sponsors:
            # Проверяем подписку через Telegram API для каждого спонсора
            all_subscribed = True
            
            for sponsor in sponsors:
                # Проверяем, есть ли у спонсора channel_id
                if hasattr(sponsor, 'channel_id') and sponsor.channel_id:
                    # Проверяем подписку через API
                    is_subscribed = await check_channel_subscription(
                        callback.bot, 
                        callback.from_user.id, 
                        sponsor.channel_id
                    )
                    
                    if not is_subscribed:
                        all_subscribed = False
                        break
                else:
                    # Если у спонсора нет channel_id, проверяем по базе данных
                    user_subscriptions = [
                        sub.sponsor_id for sub in check_user_subscription(callback.from_user.id)
                    ]
                    
                    if sponsor.id not in user_subscriptions:
                        all_subscribed = False
                        break
            
            if not all_subscribed:
                # Если пользователь не подписан на всех спонсоров, показываем сообщение
                session.close()
                await callback.answer(locale.get("gift_sponsors_required", "Чтобы получить подарок, необходимо подписаться на всех спонсоров или иметь премиум-статус."), show_alert=True)
                # Перенаправляем на страницу со спонсорами
                from keyboards.inline_keyboard import sponsors_list_keyboard, back_to_menu_keyboard
                
                text = f"{locale['sponsors_title']}\n\n{locale['sponsors_description']}\n\n{locale.get('gift_subscribe_to_sponsors', '⚠️ Подпишитесь на всех спонсоров, чтобы получить ежедневный подарок!')}"
                
                # Получаем подписки пользователя для отображения в списке
                user_subscriptions = [
                    sub.sponsor_id for sub in check_user_subscription(callback.from_user.id)
                ]
                
                # Выводим список спонсоров и кнопки
                await callback.message.edit_text(
                    text,
                    reply_markup=sponsors_list_keyboard(locale, sponsors, callback.from_user.id, user_subscriptions)
                )
                return
    
    # Если пользователь подписан на всех спонсоров или имеет премиум-статус,
    # или если нет активных спонсоров, выдаем подарок
    gift_amount = random.randint(1, 10)
    user.crystals += gift_amount
    user.last_gift = now
    session.commit()
    session.close()
    await callback.answer(locale["gift_success"].format(amount=gift_amount), show_alert=True)
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

async def process_gift_back(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_gift(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_gift(call, locale), lambda c: c.data == "gift")
    dp.register_callback_query_handler(lambda call: process_receive_gift(call, locale), lambda c: c.data == "receive_gift")
    dp.register_callback_query_handler(lambda call: process_gift_back(call, locale), lambda c: c.data == "back_to_main")
