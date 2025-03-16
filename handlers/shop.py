import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import shop_keyboard, additional_keyboard
from utils.achievements import check_and_award_achievements, check_premium_achievement
from utils.helpers import get_user_language, get_user_coins, update_user_coins, is_user_premium, set_premium_status
from database.crud import get_bot_setting
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Цены товаров
PRICES = {
    "premium_forever": 100000,
    "premium_week": 1000,
    "premium_day": 400,
    "secret_video": 2000
}

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

    # Создаем клавиатуру для подтверждения
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(
            text=locale.get("confirm", "✅ Да"),
            callback_data=f"confirm_purchase:{item_type}"
        ),
        types.InlineKeyboardButton(
            text=locale.get("cancel", "❌ Нет"),
            callback_data="shop"
        )
    )

    # Формируем текст подтверждения в зависимости от типа покупки
    if item_type == "premium_forever":
        item_name = "Премиум навсегда"
    elif item_type == "premium_week":
        item_name = "Премиум на неделю"
    elif item_type == "premium_day":
        item_name = "Премиум на день"
    elif item_type == "secret_video":
        item_name = "Секретный ролик Бубса"
    
    confirm_text = locale.get(
        "buy_secret_confirm",
        "Вы уверены, что хотите купить {name} за {price} монет?"
    ).format(name=item_name, price=price)
    
    # Отправляем сообщение с подтверждением
    await callback.message.edit_text(confirm_text, reply_markup=kb)

async def process_confirm_purchase(callback: types.CallbackQuery, locale):
    """Обработчик для подтверждения покупки"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем тип покупки из callback_data
    item_type = callback.data.split(":")[1]
    price = PRICES.get(item_type)
    
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
            # Получаем ссылку на секретное видео из настроек
            video_url = get_bot_setting("secret_video_url")
            if not video_url:
                video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Дефолтная ссылка
            
            # Отправляем новое сообщение с секретным видео
            await callback.message.answer(
                f"🎬 Секретный ролик Бубса: {video_url}",
                reply_markup=shop_keyboard(locale)
            )
            # Удаляем сообщение с подтверждением
            await callback.message.delete()
            return
        
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
        lambda c: process_confirm_purchase(c, locale),
        lambda c: c.data.startswith("confirm_purchase:")
    )
    dp.register_callback_query_handler(
        lambda c: process_back_to_additional(c, locale),
        lambda c: c.data == "back_to_additional"
    ) 