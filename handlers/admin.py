from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_IDS
from keyboards.inline_keyboard import admin_panel_keyboard, admin_premium_duration_keyboard, admin_premium_keyboard
from database.crud import update_user_premium, get_premium_prices, update_premium_price
from utils.helpers import get_user_language
import datetime
import logging

logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_duration = State()
    waiting_for_price = State()

async def cmd_admin_panel(message: types.Message, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    text = user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:")
    await message.answer(text, reply_markup=admin_panel_keyboard(user_locale))

async def process_give_premium(callback: types.CallbackQuery, state: FSMContext, locale):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(user_locale.get("enter_user_id", "Введите ID пользователя, которому хотите выдать премиум:"))
    await AdminStates.waiting_for_user_id.set()

async def process_user_id_input(message: types.Message, state: FSMContext, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    if not message.text.isdigit():
        await message.answer(user_locale.get("invalid_user_id", "❌ Пожалуйста, введите корректный ID пользователя (только цифры)"))
        return
    
    await state.update_data(user_id=int(message.text))
    await message.answer(
        user_locale.get("select_premium_duration", "Выберите длительность премиума:"), 
        reply_markup=admin_premium_duration_keyboard(user_locale)
    )
    await AdminStates.waiting_for_duration.set()

async def process_premium_duration(callback: types.CallbackQuery, state: FSMContext, locale):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return

    user_locale = get_user_language(callback.from_user.id)
    duration_mapping = {
        "premium_1month": 30,
        "premium_6months": 180,
        "premium_1year": 365,
        "premium_forever": 36500  # 100 лет
    }
    
    duration_days = duration_mapping.get(callback.data)
    if not duration_days:
        await callback.answer(user_locale.get("invalid_duration", "❌ Неверная длительность"), show_alert=True)
        return

    data = await state.get_data()
    user_id = data.get('user_id')
    
    if not user_id:
        await callback.answer(user_locale.get("user_id_not_found", "❌ Ошибка: ID пользователя не найден"), show_alert=True)
        return

    # Устанавливаем дату окончания премиума
    end_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)
    
    try:
        update_user_premium(user_id, end_date)
        await callback.answer(user_locale.get("premium_success", "✅ Премиум успешно выдан!"), show_alert=True)
        await callback.message.edit_text(
            user_locale.get("premium_given", "✅ Премиум выдан пользователю {user_id}\nДлительность: {days} дней\nДата окончания: {date}").format(
                user_id=user_id,
                days=duration_days,
                date=end_date.strftime('%d.%m.%Y')
            ),
            reply_markup=admin_panel_keyboard(user_locale)
        )
    except Exception as e:
        logger.error(f"Ошибка при выдаче премиума: {str(e)}")
        await callback.answer(user_locale.get("premium_error", "❌ Ошибка при выдаче премиума"), show_alert=True)
    
    await state.finish()

async def process_back_to_admin(callback: types.CallbackQuery, state: FSMContext, locale):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await state.finish()
    await callback.answer()
    await callback.message.edit_text(
        user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:"),
        reply_markup=admin_panel_keyboard(user_locale)
    )

async def process_admin_prices(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для управления ценами премиума"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущие цены
    prices = get_premium_prices()
    prices_dict = {price.duration_type: price.price for price in prices}
    
    # Форматируем текст с ценами
    text = user_locale["admin_price_menu"].format(
        month=prices_dict.get("month", "500"),
        half_year=prices_dict.get("half_year", "2500"),
        year=prices_dict.get("year", "4500"),
        forever=prices_dict.get("forever", "9900")
    )
    
    await callback.message.edit_text(text, reply_markup=admin_premium_keyboard(user_locale))

async def process_change_price(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для изменения конкретной цены"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем тип подписки из callback data
    duration_type = callback.data.split(":")[1]
    
    # Сохраняем тип подписки в состоянии
    await state.update_data(duration_type=duration_type)
    
    # Определяем название типа для отображения
    duration_name_mapping = {
        "month": "месяц",
        "half_year": "полгода",
        "year": "год",
        "forever": "навсегда"
    }
    
    duration_name = duration_name_mapping.get(duration_type, duration_type)
    
    await callback.message.edit_text(
        user_locale["admin_set_price_prompt"].format(duration=duration_name)
    )
    
    await AdminStates.waiting_for_price.set()

async def process_price_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода новой цены"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что введено число
    if not message.text.isdigit():
        await message.answer("❌ Введите корректное числовое значение цены")
        return
    
    new_price = int(message.text)
    
    # Получаем тип подписки из состояния
    data = await state.get_data()
    duration_type = data.get("duration_type")
    
    if not duration_type:
        await message.answer("❌ Ошибка: тип подписки не найден")
        return
    
    try:
        # Обновляем цену
        update_premium_price(duration_type, new_price)
        await message.answer(user_locale["admin_price_updated"])
        
        # Показываем обновленное меню цен
        prices = get_premium_prices()
        prices_dict = {price.duration_type: price.price for price in prices}
        
        # Форматируем текст с ценами
        text = user_locale["admin_price_menu"].format(
            month=prices_dict.get("month", "500"),
            half_year=prices_dict.get("half_year", "2500"),
            year=prices_dict.get("year", "4500"),
            forever=prices_dict.get("forever", "9900")
        )
        
        await message.answer(text, reply_markup=admin_premium_keyboard(user_locale))
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены: {str(e)}")
        await message.answer(user_locale["admin_price_error"])
    
    await state.finish()

def register_handlers_admin(dp: Dispatcher, locale):
    """Регистрация всех обработчиков админ панели"""
    dp.register_message_handler(lambda message, state: cmd_admin_panel(message, locale), commands=["panel"])
    dp.register_callback_query_handler(lambda c, state: process_give_premium(c, state, locale), lambda c: c.data == "give_premium")
    dp.register_message_handler(lambda message, state: process_user_id_input(message, state, locale), state=AdminStates.waiting_for_user_id)
    dp.register_callback_query_handler(
        lambda c, state: process_premium_duration(c, state, locale),
        lambda c: c.data.startswith("premium_"),
        state=AdminStates.waiting_for_duration
    )
    dp.register_callback_query_handler(
        lambda c, state: process_back_to_admin(c, state, locale),
        lambda c: c.data == "back_to_admin"
    )
    # Добавляем обработчики для управления ценами
    dp.register_callback_query_handler(
        lambda c, state: process_admin_prices(c, state, locale),
        lambda c: c.data == "manage_prices"
    )
    dp.register_callback_query_handler(
        lambda c, state: process_change_price(c, state, locale),
        lambda c: c.data.startswith("change_price:")
    )
    dp.register_message_handler(
        lambda message, state: process_price_input(message, state, locale),
        state=AdminStates.waiting_for_price
    ) 