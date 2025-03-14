from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import is_user_premium
from database.crud import get_premium_prices, get_user, update_user_premium, use_promo_code
from config import ADMIN_ID, MANAGER_LINK
from utils.helpers import get_user_language, record_section_visit, check_premium_achievement
from keyboards.inline_keyboard import premium_keyboard, premium_prices_keyboard
from database.session import SessionLocal
import datetime
from database.models import User
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from utils.helpers import use_promo_code
import logging

logger = logging.getLogger(__name__)

class PremiumStates(StatesGroup):
    waiting_for_price = State()

class PromoState(StatesGroup):
    """Состояния для работы с промокодами"""
    waiting_for_promo_code = State()

async def cmd_premium(message: types.Message, locale):
    """Обработчик команды /premium - показывает информацию о премиум-статусе"""
    user_locale = get_user_language(message.from_user.id)
    user = get_user(message.from_user.id)
    
    # Проверяем, есть ли у пользователя премиум-статус
    is_premium = user and user.premium_end_date and user.premium_end_date > datetime.datetime.now()
    
    if is_premium:
        # Форматируем дату окончания премиума
        premium_end = user.premium_end_date.strftime("%d.%m.%Y")
        await message.answer(
            user_locale.get("premium_active_text", "").format(date=premium_end),
            reply_markup=premium_keyboard(user_locale, is_premium=True)
        )
    else:
        await message.answer(
            user_locale.get("premium_text", ""),
            reply_markup=premium_keyboard(user_locale)
        )

async def cmd_premium_prices(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущие цены
    prices = get_premium_prices()
    
    # Словарь соответствия количества дней и типа подписки
    duration_to_type = {
        30: "month",          # 30 дней - месяц
        180: "half_year",     # 180 дней - полгода
        365: "year",          # 365 дней - год
        9999: "forever"       # 9999 дней - навсегда
    }
    
    # Преобразуем в словарь для удобства
    prices_dict = {}
    for price in prices:
        type_key = duration_to_type.get(price.duration_days, str(price.duration_days))
        prices_dict[type_key] = price.price
    
    # Форматируем текст с ценами
    text = locale["premium_prices_text"].format(
        month=prices_dict.get("month", "500"),
        half_year=prices_dict.get("half_year", "2500"),
        year=prices_dict.get("year", "4500"),
        forever=prices_dict.get("forever", "9900")
    )
    
    await callback.message.edit_text(text, reply_markup=premium_prices_keyboard(locale))

async def process_premium_menu(callback: types.CallbackQuery, locale):
    """Обработчик для меню премиум"""
    user_locale = get_user_language(callback.from_user.id)
    user = get_user(callback.from_user.id)
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "premium")
    
    # Проверяем, есть ли у пользователя премиум-статус
    is_premium = user and user.premium_end_date and user.premium_end_date > datetime.datetime.now()
    
    await callback.answer()
    
    if is_premium:
        # Форматируем дату окончания премиума
        premium_end = user.premium_end_date.strftime("%d.%m.%Y")
        await callback.message.edit_text(
            user_locale.get("premium_active_text", "").format(date=premium_end),
            reply_markup=premium_keyboard(user_locale, is_premium=True)
        )
    else:
        await callback.message.edit_text(
            user_locale.get("premium_text", ""),
            reply_markup=premium_keyboard(user_locale)
        )

async def process_activate_promo(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для активации промокода"""
    user_locale = get_user_language(callback.from_user.id)
    
    await callback.answer()
    
    await callback.message.edit_text(
        user_locale.get("promo_code_input", "🎟️ Введите промокод для активации премиум:"),
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text=user_locale.get("promo_code_cancel", "🔙 Отмена"), callback_data="cancel_promo")
        )
    )
    
    await PromoState.waiting_for_promo_code.set()

async def process_promo_code(message: types.Message, state: FSMContext, locale):
    """Обработчик для проверки и активации промокода"""
    user_locale = get_user_language(message.from_user.id)
    
    # Получаем введенный промокод и преобразуем его в верхний регистр
    promo_code = message.text.strip().upper()
    
    # Пытаемся использовать промокод
    result = use_promo_code(promo_code, message.from_user.id)
    
    # Сбрасываем состояние
    await state.finish()
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=user_locale.get("back_to_menu", "🔙 Назад в меню"), callback_data="back_to_main")
    )
    
    if result and result.get('success'):
        # Промокод успешно применен
        days = result.get('duration_days', 0)
        end_date = result.get('end_date').strftime("%d.%m.%Y") if result.get('end_date') else "неизвестно"
        
        await message.answer(
            user_locale.get("promo_code_success", "").format(days=days, date=end_date),
            reply_markup=kb
        )
    else:
        # Произошла ошибка при активации промокода
        error_code = result.get('error_code') if result else 'unknown'
        
        if error_code == 'not_found':
            error_message = user_locale.get("promo_code_not_found", f"❌ Промокод {promo_code} не найден.")
        elif error_code == 'expired':
            error_message = user_locale.get("promo_code_expired", f"❌ Срок действия промокода {promo_code} истек.")
        elif error_code == 'used':
            error_message = user_locale.get("promo_code_used", f"❌ Вы уже использовали промокод {promo_code}.")
        elif error_code == 'limit_reached':
            error_message = user_locale.get("promo_code_limit", f"❌ Лимит использования промокода {promo_code} исчерпан.")
        elif error_code == 'inactive':
            error_message = user_locale.get("promo_code_inactive", f"❌ Промокод {promo_code} неактивен.")
        else:
            error_message = user_locale.get("promo_code_error", f"❌ Произошла ошибка при активации промокода {promo_code}.")
        
        await message.answer(
            error_message,
            reply_markup=kb
        )

async def process_cancel_promo(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для отмены ввода промокода"""
    user_locale = get_user_language(callback.from_user.id)
    
    await state.finish()
    await callback.answer()
    
    # Возвращаемся в меню премиум
    await process_premium_menu(callback, locale)

def register_handlers_premium(dp: Dispatcher, locale):
    """Регистрация всех обработчиков премиум"""
    dp.register_message_handler(lambda message: cmd_premium(message, locale), commands=["premium"])
    
    # Обработчики для активации промокода
    dp.register_callback_query_handler(
        lambda c: process_premium_menu(c, locale),
        lambda c: c.data == "premium"
    )
    dp.register_callback_query_handler(
        lambda c: cmd_premium_prices(c, locale),
        lambda c: c.data == "premium_prices_info"
    )
    dp.register_callback_query_handler(
        lambda c, state: process_activate_promo(c, state, locale),
        lambda c: c.data == "activate_promo"
    )
    dp.register_message_handler(
        lambda message, state: process_promo_code(message, state, locale),
        state=PromoState.waiting_for_promo_code
    )
    dp.register_callback_query_handler(
        lambda c, state: process_cancel_promo(c, state, locale),
        lambda c: c.data == "cancel_promo",
        state=PromoState.waiting_for_promo_code
    )
