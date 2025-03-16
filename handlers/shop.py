import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import shop_keyboard, additional_keyboard
from utils.achievements import check_and_award_achievements, check_premium_achievement
from utils.helpers import get_user_language, get_user_coins, update_user_coins, is_user_premium, set_premium_status
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Цены товаров
PRICES = {
    "premium_forever": 100000,
    "premium_week": 1000,
    "premium_day": 400,
    "secret_video": 2000
}

# Секретная ссылка на видео
SECRET_VIDEO_LINK = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Замените на реальную ссылку

async def process_shop(callback: types.CallbackQuery, locale):
    """Обработчик для открытия магазина"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    text = locale["shop_text"]
    await callback.message.edit_text(text, reply_markup=shop_keyboard(locale))

async def process_shop_purchase(callback: types.CallbackQuery, locale):
    """Обработчик для покупок в магазине"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем тип покупки из callback_data
    item_type = callback.data.split(":")[1]
    price = PRICES.get(item_type)
    
    if not price:
        await callback.message.edit_text(
            locale["purchase_error"].format(error="Invalid item"),
            reply_markup=shop_keyboard(locale)
        )
        return
    
    # Проверяем баланс пользователя
    user_coins = get_user_coins(callback.from_user.id)
    if user_coins < price:
        await callback.message.edit_text(
            locale["not_enough_coins"].format(balance=user_coins, price=price),
            reply_markup=shop_keyboard(locale)
        )
        return
    
    try:
        # Списываем монеты
        if not update_user_coins(callback.from_user.id, -price):
            await callback.message.edit_text(
                locale["purchase_error"].format(error="Failed to update coins"),
                reply_markup=shop_keyboard(locale)
            )
            return
        
        # Обрабатываем разные типы покупок
        if item_type == "premium_forever":
            # Устанавливаем премиум навсегда
            set_premium_status(callback.from_user.id, None)  # None означает "навсегда"
            check_premium_achievement(callback.from_user.id)
        elif item_type == "premium_week":
            # Устанавливаем премиум на неделю
            expiry_date = datetime.now() + timedelta(days=7)
            set_premium_status(callback.from_user.id, expiry_date)
            check_premium_achievement(callback.from_user.id)
        elif item_type == "premium_day":
            # Устанавливаем премиум на день
            expiry_date = datetime.now() + timedelta(days=1)
            set_premium_status(callback.from_user.id, expiry_date)
            check_premium_achievement(callback.from_user.id)
        elif item_type == "secret_video":
            # Отправляем секретное видео
            await callback.message.answer(
                f"🎬 Секретный ролик Бубса: {SECRET_VIDEO_LINK}",
                reply_markup=shop_keyboard(locale)
            )
        
        # Отправляем сообщение об успешной покупке
        await callback.message.edit_text(
            locale["purchase_success"],
            reply_markup=shop_keyboard(locale)
        )
        
    except Exception as e:
        logger.error(f"Error processing purchase: {str(e)}")
        await callback.message.edit_text(
            locale["purchase_error"].format(error=str(e)),
            reply_markup=shop_keyboard(locale)
        )

async def process_back_to_additional(callback: types.CallbackQuery, locale):
    """Обработчик для возврата в дополнительное меню"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["additional_text"], reply_markup=additional_keyboard(locale))

def register_handlers_shop(dp: Dispatcher, locale):
    """Регистрация обработчиков магазина"""
    dp.register_callback_query_handler(
        lambda c: process_shop(c, locale),
        lambda c: c.data == "shop"
    )
    dp.register_callback_query_handler(
        lambda c: process_shop_purchase(c, locale),
        lambda c: c.data.startswith("shop_buy:")
    )
    dp.register_callback_query_handler(
        lambda c: process_back_to_additional(c, locale),
        lambda c: c.data == "back_to_additional"
    ) 