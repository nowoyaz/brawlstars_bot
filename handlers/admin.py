from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_IDS
from keyboards.inline_keyboard import admin_panel_keyboard, admin_premium_duration_keyboard, admin_premium_keyboard, admin_sponsors_keyboard, admin_sponsor_item_keyboard, admin_sponsor_confirm_delete_keyboard
from database.crud import update_user_premium, get_premium_prices, update_premium_price, get_sponsors, add_sponsor, update_sponsor, delete_sponsor
from utils.helpers import get_user_language
import datetime
import logging

logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_duration = State()
    waiting_for_price = State()
    
    # Состояния для спонсоров
    waiting_for_sponsor_name = State()
    waiting_for_sponsor_link = State()
    waiting_for_sponsor_channel_id = State()
    waiting_for_sponsor_reward = State()
    editing_sponsor = State()

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

# Обработчики для спонсоров
async def process_manage_sponsors(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для управления спонсорами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем список спонсоров
    sponsors = get_sponsors(only_active=False)
    
    if not sponsors:
        text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['no_sponsors']}"
    else:
        text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['admin_sponsors_list']}"
        for i, sponsor in enumerate(sponsors, 1):
            status = user_locale["admin_sponsor_active"] if sponsor.is_active else user_locale["admin_sponsor_inactive"]
            text += f"\n{i}. {user_locale['admin_sponsor_item'].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)}"
            # Добавляем кнопки управления для каждого спонсора
            keyboard = admin_sponsor_item_keyboard(user_locale, sponsor.id)
            # Отправляем отдельное сообщение для каждого спонсора с кнопками
            if i == 1:
                await callback.message.edit_text(text, reply_markup=keyboard)
            else:
                await callback.message.answer(f"{i}. {user_locale['admin_sponsor_item'].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)}", reply_markup=keyboard)
        return
    
    await callback.message.edit_text(text, reply_markup=admin_sponsors_keyboard(user_locale))

async def process_add_sponsor(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для добавления спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    await callback.message.edit_text(f"{user_locale['admin_add_sponsor_title']}\n\n{user_locale['admin_add_sponsor_name']}")
    await AdminStates.waiting_for_sponsor_name.set()

async def process_sponsor_name_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода имени спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем имя спонсора
    await state.update_data(sponsor_name=message.text)
    
    await message.answer(user_locale["admin_add_sponsor_link"])
    await AdminStates.waiting_for_sponsor_link.set()

async def process_sponsor_link_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода ссылки на спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем ссылку на спонсора
    await state.update_data(sponsor_link=message.text)
    
    await message.answer(user_locale["admin_add_sponsor_channel_id"])
    await AdminStates.waiting_for_sponsor_channel_id.set()

async def process_sponsor_channel_id_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода ID канала спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем ID канала, если был введен (может быть '-' для пропуска)
    channel_id = None if message.text == '-' else message.text
    await state.update_data(sponsor_channel_id=channel_id)
    
    await message.answer(user_locale["admin_add_sponsor_reward"])
    await AdminStates.waiting_for_sponsor_reward.set()

async def process_sponsor_reward_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода награды за подписку на спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что введено число
    if not message.text.isdigit():
        await message.answer("❌ Введите корректное числовое значение награды")
        return
    
    reward = int(message.text)
    
    # Получаем ранее введенные данные
    data = await state.get_data()
    name = data.get("sponsor_name")
    link = data.get("sponsor_link")
    channel_id = data.get("sponsor_channel_id")
    
    # Добавляем спонсора
    try:
        add_sponsor(name, link, reward, channel_id)
        await message.answer(user_locale["admin_sponsor_added"])
        
        # Показываем обновленный список спонсоров
        sponsors = get_sponsors(only_active=False)
        
        if not sponsors:
            text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['no_sponsors']}"
        else:
            text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['admin_sponsors_list']}"
            for sponsor in sponsors:
                status = user_locale["admin_sponsor_active"] if sponsor.is_active else user_locale["admin_sponsor_inactive"]
                text += f"\n• {user_locale['admin_sponsor_item'].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)}"
        
        await message.answer(text, reply_markup=admin_sponsors_keyboard(user_locale))
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении спонсора: {str(e)}")
        await message.answer(f"❌ Ошибка при добавлении спонсора: {str(e)}")
    
    # Сбрасываем состояние
    await state.finish()

async def process_toggle_sponsor(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для изменения статуса спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Получаем спонсора
    sponsors = get_sponsors(only_active=False)
    sponsor = next((s for s in sponsors if s.id == sponsor_id), None)
    
    if not sponsor:
        await callback.answer(user_locale["sponsor_not_found"], show_alert=True)
        return
    
    # Изменяем статус спонсора
    try:
        update_sponsor(sponsor_id, is_active=not sponsor.is_active)
        await callback.answer(user_locale["admin_sponsor_toggle"], show_alert=True)
        
        # Обновляем сообщение
        status = user_locale["admin_sponsor_inactive"] if sponsor.is_active else user_locale["admin_sponsor_active"]
        text = user_locale["admin_sponsor_item"].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)
        await callback.message.edit_text(text, reply_markup=admin_sponsor_item_keyboard(user_locale, sponsor_id))
        
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса спонсора: {str(e)}")
        await callback.answer("❌ Произошла ошибка при изменении статуса спонсора", show_alert=True)

async def process_delete_sponsor_confirm(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для подтверждения удаления спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Запрашиваем подтверждение
    await callback.message.edit_text(
        user_locale["admin_confirm_delete_sponsor"],
        reply_markup=admin_sponsor_confirm_delete_keyboard(user_locale, sponsor_id)
    )

async def process_confirm_delete_sponsor(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для удаления спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Удаляем спонсора
    try:
        delete_sponsor(sponsor_id)
        await callback.answer(user_locale["admin_sponsor_deleted"], show_alert=True)
        
        # Возвращаемся к списку спонсоров
        await process_manage_sponsors(callback, state, locale)
        
    except Exception as e:
        logger.error(f"Ошибка при удалении спонсора: {str(e)}")
        await callback.answer("❌ Произошла ошибка при удалении спонсора", show_alert=True)

async def process_cancel_delete_sponsor(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для отмены удаления спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    
    # Получаем ID спонсора из callback_data
    sponsor_id = int(callback.data.split(":")[1])
    
    # Получаем спонсора
    sponsors = get_sponsors(only_active=False)
    sponsor = next((s for s in sponsors if s.id == sponsor_id), None)
    
    if sponsor:
        # Возвращаемся к просмотру спонсора
        status = user_locale["admin_sponsor_active"] if sponsor.is_active else user_locale["admin_sponsor_inactive"]
        text = user_locale["admin_sponsor_item"].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)
        await callback.message.edit_text(text, reply_markup=admin_sponsor_item_keyboard(user_locale, sponsor_id))
    else:
        # Если спонсор не найден, возвращаемся к списку спонсоров
        await process_manage_sponsors(callback, state, locale)

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
    
    # Регистрация обработчиков для спонсоров
    dp.register_callback_query_handler(
        lambda c, state: process_manage_sponsors(c, state, locale),
        lambda c: c.data == "manage_sponsors"
    )
    dp.register_callback_query_handler(
        lambda c, state: process_add_sponsor(c, state, locale),
        lambda c: c.data == "add_sponsor"
    )
    dp.register_message_handler(
        lambda message, state: process_sponsor_name_input(message, state, locale),
        state=AdminStates.waiting_for_sponsor_name
    )
    dp.register_message_handler(
        lambda message, state: process_sponsor_link_input(message, state, locale),
        state=AdminStates.waiting_for_sponsor_link
    )
    dp.register_message_handler(
        lambda message, state: process_sponsor_channel_id_input(message, state, locale),
        state=AdminStates.waiting_for_sponsor_channel_id
    )
    dp.register_message_handler(
        lambda message, state: process_sponsor_reward_input(message, state, locale),
        state=AdminStates.waiting_for_sponsor_reward
    )
    dp.register_callback_query_handler(
        lambda c, state: process_toggle_sponsor(c, state, locale),
        lambda c: c.data.startswith("toggle_sponsor:")
    )
    dp.register_callback_query_handler(
        lambda c, state: process_delete_sponsor_confirm(c, state, locale),
        lambda c: c.data.startswith("delete_sponsor:")
    )
    dp.register_callback_query_handler(
        lambda c, state: process_confirm_delete_sponsor(c, state, locale),
        lambda c: c.data.startswith("confirm_delete_sponsor:")
    )
    dp.register_callback_query_handler(
        lambda c, state: process_cancel_delete_sponsor(c, state, locale),
        lambda c: c.data.startswith("cancel_delete_sponsor:")
    ) 