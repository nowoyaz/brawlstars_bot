from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_IDS
from keyboards.inline_keyboard import admin_panel_keyboard, admin_premium_duration_keyboard
from database.crud import update_user_premium
from utils.helpers import get_user_language
import datetime
import logging

logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_duration = State()

async def cmd_admin_panel(message: types.Message, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = await get_user_language(message.from_user.id)
    text = user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:")
    await message.answer(text, reply_markup=admin_panel_keyboard(user_locale))

async def process_give_premium(callback: types.CallbackQuery, state: FSMContext, locale):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = await get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(user_locale.get("enter_user_id", "Введите ID пользователя, которому хотите выдать премиум:"))
    await AdminStates.waiting_for_user_id.set()

async def process_user_id_input(message: types.Message, state: FSMContext, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = await get_user_language(message.from_user.id)
    
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

    user_locale = await get_user_language(callback.from_user.id)
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
        await update_user_premium(user_id, end_date)
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
    
    user_locale = await get_user_language(callback.from_user.id)
    await state.finish()
    await callback.answer()
    await callback.message.edit_text(
        user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:"),
        reply_markup=admin_panel_keyboard(user_locale)
    )

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