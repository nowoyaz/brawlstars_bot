from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_IDS
from keyboards.inline_keyboard import admin_panel_keyboard, admin_premium_duration_keyboard, admin_premium_keyboard, admin_sponsors_keyboard, admin_sponsor_item_keyboard, admin_sponsor_confirm_delete_keyboard, admin_keyboard, back_to_admin_keyboard
from database.crud import update_user_premium, get_premium_prices, update_premium_price, get_sponsors, add_sponsor, update_sponsor, delete_sponsor, add_promo_code, get_promo_codes, delete_promo_code, deactivate_promo_code, get_user_by_tg_id, update_user_coins, update_promo_code
from utils.helpers import get_user_language
import datetime
import logging
from aiogram.utils.exceptions import MessageNotModified

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
    
    # Состояния для промокодов
    waiting_for_promo_code = State()
    waiting_for_promo_duration = State()
    waiting_for_promo_uses = State()
    waiting_for_promo_expiry = State()

class AdminGiveCrystalsStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

async def cmd_admin_panel(message: types.Message, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    text = user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:")
    await message.answer(text, reply_markup=admin_panel_keyboard(user_locale))

async def process_give_crystals(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик кнопки выдачи монет"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return

    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Создаем клавиатуру с кнопкой отмены
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="back_to_admin"))
    
    await state.set_state(AdminGiveCrystalsStates.waiting_for_user_id)
    await callback.message.answer(user_locale["admin_enter_user_id"], reply_markup=kb)

async def process_user_id_for_crystals(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода ID пользователя для выдачи монет"""
    if message.from_user.id not in ADMIN_IDS:
        return

    user_locale = get_user_language(message.from_user.id)
    
    try:
        user_id = int(message.text)
        user = get_user_by_tg_id(user_id)
        
        if not user:
            await message.answer(user_locale["admin_user_not_found"].format(user_id=user_id))
            return
            
        await state.update_data(target_user_id=user_id)
        await state.set_state(AdminGiveCrystalsStates.waiting_for_amount)
        await message.answer(user_locale["admin_enter_crystals_amount"])
        
    except ValueError:
        await message.answer(user_locale["error_invalid_recipient"])

async def process_crystals_amount(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода количества монет"""
    if message.from_user.id not in ADMIN_IDS:
        return

    user_locale = get_user_language(message.from_user.id)
    
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer(user_locale["admin_invalid_amount"])
            return
            
        data = await state.get_data()
        target_user_id = data.get("target_user_id")
        
        if update_user_coins(target_user_id, amount):
            await message.answer(user_locale["admin_crystals_given"].format(
                user_id=target_user_id,
                amount=amount
            ))
        else:
            await message.answer(user_locale["admin_user_not_found"].format(user_id=target_user_id))
            
        await state.finish()
        await message.answer(
            user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:"),
            reply_markup=admin_panel_keyboard(user_locale)
        )
        
    except ValueError:
        await message.answer(user_locale["admin_invalid_amount"])

async def process_give_premium(callback: types.CallbackQuery, state: FSMContext, locale):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Создаем клавиатуру с кнопкой отмены
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="back_to_admin"))
    
    await callback.message.edit_text(
        user_locale.get("enter_user_id", "Введите ID пользователя, которому хотите выдать премиум:"),
        reply_markup=kb
    )
    await AdminStates.waiting_for_user_id.set()

async def process_user_id_input(message: types.Message, state: FSMContext, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    if not message.text.isdigit():
        # Создаем клавиатуру с кнопкой отмены
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="back_to_admin"))
        
        await message.answer(
            user_locale.get("invalid_user_id", "❌ Пожалуйста, введите корректный ID пользователя (только цифры)"),
            reply_markup=kb
        )
        return
    
    await state.update_data(user_id=int(message.text))
    
    # Добавляем кнопку отмены к клавиатуре с длительностями
    kb = admin_premium_duration_keyboard(user_locale)
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="back_to_admin"))
    
    await message.answer(
        user_locale.get("select_premium_duration", "Выберите длительность премиума:"),
        reply_markup=kb
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
        
        # Создаем клавиатуру с кнопкой "Назад"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"), callback_data="back_to_admin"))
        
        await callback.message.edit_text(
            user_locale.get("premium_given", "✅ Премиум выдан пользователю {user_id}\nДлительность: {days} дней\nДата окончания: {date}").format(
                user_id=user_id,
                days=duration_days,
                date=end_date.strftime('%d.%m.%Y')
            ),
            reply_markup=kb
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
    
    try:
        if callback.data == "back_to_admin":
            text = user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:")
            await callback.message.edit_text(text, reply_markup=admin_panel_keyboard(user_locale))
        elif callback.data == "manage_promo_codes":
            # Удаляем текущее сообщение и отправляем новое для избежания ошибки MessageNotModified
            await callback.message.delete()
            await process_manage_promo_codes(callback, state, locale)
        elif callback.data == "manage_sponsors":
            # Удаляем текущее сообщение и отправляем новое для избежания ошибки MessageNotModified
            await callback.message.delete()
            await process_manage_sponsors(callback, state, locale)
    except MessageNotModified:
        await callback.answer(user_locale.get("no_changes", "Изменений нет"), show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при возврате в админ-панель: {str(e)}")
        # Создаем новое сообщение в случае ошибки
        text = user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:")
        await callback.message.answer(text, reply_markup=admin_panel_keyboard(user_locale))

async def process_admin_prices(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для управления ценами премиума"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        # Получаем текущие цены
        prices = get_premium_prices()
        prices_dict = {}
        
        # Преобразуем цены в словарь
        duration_mapping = {
            30: "month",
            180: "half_year",
            365: "year",
            36500: "forever"
        }
        
        for price_obj in prices:
            try:
                duration_type = duration_mapping.get(price_obj.duration_days)
                if duration_type:
                    prices_dict[duration_type] = price_obj.price
            except AttributeError as e:
                logger.error(f"Ошибка при получении атрибутов цены: {str(e)}")
                continue
        
        # Создаем клавиатуру для управления ценами
        kb = types.InlineKeyboardMarkup(row_width=1)
        
        # Добавляем кнопки для изменения цен
        kb.add(
            types.InlineKeyboardButton(
                text=f"💰 Месяц ({prices_dict.get('month', '500')}₽)", 
                callback_data="change_price:month"
            ),
            types.InlineKeyboardButton(
                text=f"💰 Полгода ({prices_dict.get('half_year', '2500')}₽)", 
                callback_data="change_price:half_year"
            ),
            types.InlineKeyboardButton(
                text=f"💰 Год ({prices_dict.get('year', '4500')}₽)", 
                callback_data="change_price:year"
            ),
            types.InlineKeyboardButton(
                text=f"💰 Навсегда ({prices_dict.get('forever', '9900')}₽)", 
                callback_data="change_price:forever"
            )
        )
        
        # Добавляем кнопку возврата
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"),
            callback_data="back_to_admin"
        ))
        
        # Формируем текст с текущими ценами
        text = "💵 Управление ценами\n\n"
        text += f"Текущие цены:\n"
        text += f"• Месяц: {prices_dict.get('month', '500')}₽\n"
        text += f"• Полгода: {prices_dict.get('half_year', '2500')}₽\n"
        text += f"• Год: {prices_dict.get('year', '4500')}₽\n"
        text += f"• Навсегда: {prices_dict.get('forever', '9900')}₽\n\n"
        text += "Нажмите на кнопку с ценой, чтобы изменить её"
        
        # Удаляем текущее сообщение и отправляем новое
        await callback.message.edit_text(text, reply_markup=kb)
        
    except MessageNotModified:
        await callback.answer(user_locale.get("no_changes", "Изменений нет"), show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при управлении ценами: {str(e)}")
        # В случае ошибки отправляем новое сообщение
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"),
            callback_data="back_to_admin"
        ))
        await callback.message.answer(
            user_locale.get("error_loading_prices", "❌ Ошибка при загрузке цен"),
            reply_markup=kb
        )

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
    
    # Определяем количество дней для каждого типа
    duration_days_mapping = {
        "month": 30,
        "half_year": 180,
        "year": 365,
        "forever": 36500
    }
    
    duration_name = duration_name_mapping.get(duration_type, duration_type)
    duration_days = duration_days_mapping.get(duration_type)
    
    # Получаем текущую цену
    prices = get_premium_prices()
    current_price = None
    for price in prices:
        if price.duration_days == duration_days:
            current_price = price.price
            break
    
    # Создаем клавиатуру с кнопкой отмены
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="premium_prices"))
    
    text = f"💵 Изменение цены для периода: {duration_name}\n"
    if current_price is not None:
        text += f"Текущая цена: {current_price}₽\n"
    text += "\nВведите новую цену (только число):"
    
    await callback.message.edit_text(text, reply_markup=kb)
    await AdminStates.waiting_for_price.set()

async def process_price_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода новой цены"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что введено число
    if not message.text.isdigit() or int(message.text) <= 0:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="premium_prices"))
        
        await message.answer(
            user_locale.get("admin_invalid_price", "❌ Цена должна быть положительным числом. Попробуйте еще раз:"),
            reply_markup=kb
        )
        return
    
    new_price = int(message.text)
    
    # Получаем тип подписки из состояния
    data = await state.get_data()
    duration_type = data.get("duration_type")
    
    if not duration_type:
        await message.answer("❌ Ошибка: тип подписки не найден")
        await state.finish()
        return
    
    # Маппинг типов подписки на количество дней
    duration_days_mapping = {
        "month": 30,
        "half_year": 180,
        "year": 365,
        "forever": 36500
    }
    
    duration_days = duration_days_mapping.get(duration_type)
    if not duration_days:
        await message.answer("❌ Ошибка: неверный тип подписки")
        await state.finish()
        return
    
    try:
        # Обновляем цену
        update_premium_price(duration_days, new_price)
        await message.answer(user_locale.get("admin_price_updated", "✅ Цена успешно обновлена"))
        
        # Возвращаемся к управлению ценами
        await process_admin_prices(
            types.CallbackQuery(
                id="temp",
                from_user=message.from_user,
                chat_instance="temp",
                message=message,
                data="premium_prices"
            ),
            state,
            locale
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены: {str(e)}")
        await message.answer(user_locale.get("admin_price_error", "❌ Ошибка при обновлении цены"))
    
    await state.finish()

# Обработчики для спонсоров
async def process_manage_sponsors(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для управления спонсорами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        # Получаем список спонсоров
        sponsors = get_sponsors(is_active_only=False)
        
        # Создаем базовую клавиатуру
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_add_sponsor", "➕ Добавить спонсора"), callback_data="add_sponsor"))
        kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"), callback_data="back_to_admin"))
        
        if not sponsors:
            text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['no_sponsors']}"
            await callback.message.answer(text, reply_markup=kb)
            return
        
        # Отправляем заголовок со списком спонсоров
        text = f"{user_locale['admin_sponsors_title']}\n\n{user_locale['admin_sponsors_list']}"
        await callback.message.answer(text, reply_markup=kb)
        
        # Отправляем отдельные сообщения для каждого спонсора
        for i, sponsor in enumerate(sponsors, 1):
            status = user_locale["admin_sponsor_active"] if sponsor.is_active else user_locale["admin_sponsor_inactive"]
            sponsor_text = f"{i}. {user_locale['admin_sponsor_item'].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)}"
            keyboard = admin_sponsor_item_keyboard(user_locale, sponsor.id)
            await callback.message.answer(sponsor_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Ошибка при отображении спонсоров: {str(e)}")
        # В случае ошибки отправляем новое сообщение
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"), callback_data="back_to_admin"))
        await callback.message.answer(
            user_locale.get("error_loading_sponsors", "❌ Ошибка при загрузке списка спонсоров"),
            reply_markup=kb
        )

async def process_add_sponsor(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для добавления спонсора"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Добавляем кнопку "Назад"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад"), callback_data="manage_sponsors"))
    
    await callback.message.edit_text(
        f"{user_locale['admin_add_sponsor_title']}\n\n{user_locale['admin_add_sponsor_name']}",
        reply_markup=kb
    )
    await AdminStates.waiting_for_sponsor_name.set()

async def process_sponsor_name_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода имени спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем имя спонсора
    await state.update_data(sponsor_name=message.text)
    
    # Добавляем кнопку "Назад"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад"), callback_data="manage_sponsors"))
    
    await message.answer(user_locale["admin_add_sponsor_link"], reply_markup=kb)
    await AdminStates.waiting_for_sponsor_link.set()

async def process_sponsor_link_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода ссылки на спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем ссылку на спонсора
    await state.update_data(sponsor_link=message.text)
    
    # Добавляем кнопку "Назад"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад"), callback_data="manage_sponsors"))
    
    await message.answer(user_locale["admin_add_sponsor_channel_id"], reply_markup=kb)
    await AdminStates.waiting_for_sponsor_channel_id.set()

async def process_sponsor_channel_id_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода ID канала спонсора"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Сохраняем ID канала, если был введен (может быть '-' для пропуска)
    channel_id = None if message.text == '-' else message.text
    await state.update_data(sponsor_channel_id=channel_id)
    
    # Добавляем кнопку "Назад"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад"), callback_data="manage_sponsors"))
    
    await message.answer(user_locale["admin_add_sponsor_reward"], reply_markup=kb)
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
        sponsors = get_sponsors(is_active_only=False)
        
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
    sponsors = get_sponsors(is_active_only=False)
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
    sponsors = get_sponsors(is_active_only=False)
    sponsor = next((s for s in sponsors if s.id == sponsor_id), None)
    
    if sponsor:
        # Возвращаемся к просмотру спонсора
        status = user_locale["admin_sponsor_active"] if sponsor.is_active else user_locale["admin_sponsor_inactive"]
        text = user_locale["admin_sponsor_item"].format(name=sponsor.name, link=sponsor.link, reward=sponsor.reward, status=status)
        await callback.message.edit_text(text, reply_markup=admin_sponsor_item_keyboard(user_locale, sponsor_id))
    else:
        # Если спонсор не найден, возвращаемся к списку спонсоров
        await process_manage_sponsors(callback, state, locale)

# Обработчики для промокодов

async def process_manage_promo_codes(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для управления промокодами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем список промокодов
    promo_codes = get_promo_codes(include_inactive=True)
    
    # Создаем клавиатуру
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_add_promo", "➕ Добавить промокод"), callback_data="add_promo_code"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"), callback_data="back_to_admin"))
    
    if not promo_codes:
        text = user_locale.get("admin_promo_title", "🎟️ Управление промокодами") + "\n\n" + user_locale.get("no_promo_codes", "Промокоды не найдены.")
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except MessageNotModified:
            await callback.answer(user_locale.get("no_changes", "Изменений нет"), show_alert=True)
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {str(e)}")
            await callback.message.answer(text, reply_markup=kb)
        return
    
    # Формируем текст со списком промокодов
    text = user_locale.get("admin_promo_title", "🎟️ Управление промокодами") + "\n\n" + user_locale.get("admin_promo_list", "Список промокодов:")
    
    try:
        # Сначала отправляем основное сообщение со списком
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except MessageNotModified:
            await callback.answer(user_locale.get("no_changes", "Изменений нет"), show_alert=True)
            return
        except Exception as e:
            logger.error(f"Ошибка при обновлении основного сообщения: {str(e)}")
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        
        # Затем отправляем отдельные сообщения для каждого промокода
        for i, promo in enumerate(promo_codes, 1):
            status = user_locale.get("active", "✓ Активен") if promo.is_active else user_locale.get("inactive", "✗ Неактивен")
            
            if promo.expires_at:
                expiry_date = promo.expires_at.strftime("%d.%m.%Y")
                expiry_text = user_locale.get("promo_expires", "до {date}").format(date=expiry_date)
            else:
                expiry_text = user_locale.get("promo_no_expiry", "бессрочно")
            
            promo_text = f"{i}. <code>{promo.code}</code> ({promo.duration_days} дн., {expiry_text}) - {status} [{promo.uses_count}/{promo.max_uses}]"
            
            # Создаем клавиатуру для каждого промокода
            promo_kb = types.InlineKeyboardMarkup(row_width=2)
            
            if promo.is_active:
                promo_kb.insert(types.InlineKeyboardButton(
                    text=user_locale.get("button_deactivate_promo", "🚫 Деактивировать"), 
                    callback_data=f"deactivate_promo:{promo.id}"
                ))
            else:
                promo_kb.insert(types.InlineKeyboardButton(
                    text=user_locale.get("button_activate_promo", "✅ Активировать"), 
                    callback_data=f"activate_promo:{promo.id}"
                ))
            
            promo_kb.insert(types.InlineKeyboardButton(
                text=user_locale.get("button_delete_promo", "🗑️ Удалить"), 
                callback_data=f"delete_promo:{promo.id}"
            ))
            
            await callback.message.answer(promo_text, reply_markup=promo_kb, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Ошибка при отображении промокодов: {str(e)}")
        await callback.message.answer(
            user_locale.get("error_loading_promo_codes", "❌ Ошибка при загрузке промокодов"),
            reply_markup=kb
        )

async def process_add_promo_code(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для добавления нового промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await callback.message.edit_text(
        user_locale.get("admin_add_promo_code", "🎟️ Добавление нового промокода") + 
        "\n\n" + 
        user_locale.get("admin_enter_promo_code", "Введите текст промокода (только латинские буквы и цифры):"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_code.set()

async def process_promo_code_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода текста промокода"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что промокод корректный (только латинские буквы и цифры)
    promo_code = message.text.strip().upper()
    if not promo_code.isalnum():
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
        
        await message.answer(
            user_locale.get("admin_invalid_promo_code", "❌ Промокод должен содержать только латинские буквы и цифры. Попробуйте еще раз:"),
            reply_markup=kb
        )
        return
    
    # Сохраняем промокод в состоянии
    await state.update_data(promo_code=promo_code)
    
    # Запрашиваем срок действия премиума
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text="7 дней", callback_data="promo_duration:7"),
        types.InlineKeyboardButton(text="30 дней", callback_data="promo_duration:30"),
        types.InlineKeyboardButton(text="90 дней", callback_data="promo_duration:90"),
        types.InlineKeyboardButton(text="365 дней", callback_data="promo_duration:365")
    )
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_custom", "Другой срок"), callback_data="promo_duration:custom"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await message.answer(
        user_locale.get("admin_enter_promo_duration", "Выберите срок действия премиума по промокоду:"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_duration.set()

async def process_promo_duration_selection(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик выбора срока действия промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем выбранный срок
    duration_str = callback.data.split(":")[1]
    
    if duration_str == "custom":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
        
        await callback.message.edit_text(
            user_locale.get("admin_enter_custom_duration", "Введите срок действия промокода в днях (только число):"),
            reply_markup=kb
        )
        return
    
    # Сохраняем срок действия в состоянии
    await state.update_data(promo_duration=int(duration_str))
    
    # Запрашиваем количество использований
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text="1 раз", callback_data="promo_uses:1"),
        types.InlineKeyboardButton(text="5 раз", callback_data="promo_uses:5"),
        types.InlineKeyboardButton(text="10 раз", callback_data="promo_uses:10"),
        types.InlineKeyboardButton(text="100 раз", callback_data="promo_uses:100")
    )
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_custom", "Другое количество"), callback_data="promo_uses:custom"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await callback.message.edit_text(
        user_locale.get("admin_enter_promo_uses", "Выберите максимальное количество использований промокода:"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_uses.set()

async def process_promo_uses_selection(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик выбора количества использований промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем выбранное количество использований
    uses_str = callback.data.split(":")[1]
    
    if uses_str == "custom":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
        
        await callback.message.edit_text(
            user_locale.get("admin_enter_custom_uses", "Введите максимальное количество использований промокода (только число):"),
            reply_markup=kb
        )
        return
    
    # Сохраняем количество использований в состоянии
    await state.update_data(promo_uses=int(uses_str))
    
    # Запрашиваем срок действия самого промокода
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_no_expiry", "Бессрочно"), callback_data="promo_expiry:none"))
    kb.add(types.InlineKeyboardButton(text="7 дней", callback_data="promo_expiry:7"))
    kb.add(types.InlineKeyboardButton(text="30 дней", callback_data="promo_expiry:30"))
    kb.add(types.InlineKeyboardButton(text="90 дней", callback_data="promo_expiry:90"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await callback.message.edit_text(
        user_locale.get("admin_enter_promo_expiry", "Выберите срок действия самого промокода (через сколько дней он станет недействительным):"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_expiry.set()

async def process_promo_expiry_selection(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик выбора срока действия самого промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        promo_code = data.get("promo_code")
        promo_duration = data.get("promo_duration")
        promo_uses = data.get("promo_uses")
        
        if not all([promo_code, promo_duration, promo_uses]):
            raise ValueError("Отсутствуют необходимые данные для создания промокода")
        
        # Получаем выбранный срок действия промокода
        expiry_str = callback.data.split(":")[1]
        expiry_date = None
        
        if expiry_str != "none":
            days = int(expiry_str)
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
        
        # Создаем промокод
        promo = add_promo_code(promo_code, promo_duration, promo_uses, expiry_date)
        
        # Формируем клавиатуру для возврата
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        
        if promo:
            # Формируем текст успешного создания
            expiry_text = user_locale.get("promo_no_expiry", "бессрочно") if not expiry_date else expiry_date.strftime("%d.%m.%Y")
            success_text = [
                user_locale.get("admin_promo_created", "✅ Промокод успешно создан:"),
                f"\n\n<code>{promo_code}</code>\n",
                user_locale.get("admin_promo_details", "Детали:"),
                f"• {user_locale.get('admin_promo_duration', 'Срок действия премиума')}: {promo_duration} дней",
                f"• {user_locale.get('admin_promo_uses', 'Лимит использований')}: {promo_uses}",
                f"• {user_locale.get('admin_promo_expiry', 'Срок действия промокода')}: {expiry_text}"
            ]
            await callback.message.edit_text(
                "\n".join(success_text),
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                user_locale.get("admin_promo_error", "❌ Ошибка при создании промокода. Возможно, такой промокод уже существует."),
                reply_markup=kb
            )
    except Exception as e:
        logger.error(f"Ошибка при создании промокода: {str(e)}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        await callback.message.edit_text(
            user_locale.get("admin_promo_error", "❌ Ошибка при создании промокода: ") + str(e),
            reply_markup=kb
        )
    finally:
        await state.finish()

async def process_delete_promo(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для удаления промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        promo_id = int(callback.data.split(":")[1])
        success = delete_promo_code(promo_id)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        
        if success:
            text = user_locale.get("admin_promo_deleted", "✅ Промокод успешно удален")
        else:
            text = user_locale.get("admin_promo_delete_error", "❌ Ошибка при удалении промокода")
        
        await callback.message.edit_text(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка при удалении промокода: {str(e)}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        await callback.message.edit_text(
            user_locale.get("admin_promo_delete_error", "❌ Ошибка при удалении промокода"),
            reply_markup=kb
        )

async def process_deactivate_promo(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для деактивации промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        promo_id = int(callback.data.split(":")[1])
        success = deactivate_promo_code(promo_id)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        
        if success:
            text = user_locale.get("admin_promo_deactivated", "✅ Промокод успешно деактивирован")
        else:
            text = user_locale.get("admin_promo_deactivate_error", "❌ Ошибка при деактивации промокода")
        
        await callback.message.edit_text(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка при деактивации промокода: {str(e)}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        await callback.message.edit_text(
            user_locale.get("admin_promo_deactivate_error", "❌ Ошибка при деактивации промокода"),
            reply_markup=kb
        )

# Добавляем обработчик отмены для всех состояний админ-панели
async def process_cancel_premium(message: types.Message, state: FSMContext, locale):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if message.text.lower() in ["отмена", "🔙", "/cancel"]:
        user_locale = get_user_language(message.from_user.id)
        await state.finish()
        await message.answer(
            user_locale.get("admin_panel_text", "👑 Админ-панель\n\nВыберите действие:"),
            reply_markup=admin_panel_keyboard(user_locale)
        )

async def process_custom_duration_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода произвольного срока действия промокода"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что введено число
    if not message.text.isdigit() or int(message.text) <= 0:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
        
        await message.answer(
            user_locale.get("admin_invalid_duration", "❌ Срок действия должен быть положительным числом. Попробуйте еще раз:"),
            reply_markup=kb
        )
        return
    
    # Сохраняем срок действия в состоянии
    await state.update_data(promo_duration=int(message.text))
    
    # Запрашиваем количество использований
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text="1 раз", callback_data="promo_uses:1"),
        types.InlineKeyboardButton(text="5 раз", callback_data="promo_uses:5"),
        types.InlineKeyboardButton(text="10 раз", callback_data="promo_uses:10"),
        types.InlineKeyboardButton(text="100 раз", callback_data="promo_uses:100")
    )
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_custom", "Другое количество"), callback_data="promo_uses:custom"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await message.answer(
        user_locale.get("admin_enter_promo_uses", "Выберите максимальное количество использований промокода:"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_uses.set()

async def process_custom_uses_input(message: types.Message, state: FSMContext, locale):
    """Обработчик ввода произвольного количества использований промокода"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_locale = get_user_language(message.from_user.id)
    
    # Проверяем, что введено число
    if not message.text.isdigit() or int(message.text) <= 0:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
        
        await message.answer(
            user_locale.get("admin_invalid_uses", "❌ Количество использований должно быть положительным числом. Попробуйте еще раз:"),
            reply_markup=kb
        )
        return
    
    # Сохраняем количество использований в состоянии
    await state.update_data(promo_uses=int(message.text))
    
    # Запрашиваем срок действия самого промокода
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_no_expiry", "Бессрочно"), callback_data="promo_expiry:none"))
    kb.add(types.InlineKeyboardButton(text="7 дней", callback_data="promo_expiry:7"))
    kb.add(types.InlineKeyboardButton(text="30 дней", callback_data="promo_expiry:30"))
    kb.add(types.InlineKeyboardButton(text="90 дней", callback_data="promo_expiry:90"))
    kb.add(types.InlineKeyboardButton(text=user_locale.get("button_cancel", "🔙 Отмена"), callback_data="manage_promo_codes"))
    
    await message.answer(
        user_locale.get("admin_enter_promo_expiry", "Выберите срок действия самого промокода (через сколько дней он станет недействительным):"),
        reply_markup=kb
    )
    
    await AdminStates.waiting_for_promo_expiry.set()

async def process_activate_promo(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для активации промокода"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return
    
    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        promo_id = int(callback.data.split(":")[1])
        success = update_promo_code(promo_id, is_active=True)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        
        if success:
            text = user_locale.get("admin_promo_activated", "✅ Промокод успешно активирован")
        else:
            text = user_locale.get("admin_promo_activate_error", "❌ Ошибка при активации промокода")
        
        await callback.message.edit_text(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка при активации промокода: {str(e)}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_promo_management", "🔙 К управлению промокодами"),
            callback_data="manage_promo_codes"
        ))
        await callback.message.edit_text(
            user_locale.get("admin_promo_activate_error", "❌ Ошибка при активации промокода"),
            reply_markup=kb
        )

async def process_give_price(callback: types.CallbackQuery, state: FSMContext, locale):
    """Обработчик для выдачи цен"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет доступа к этой функции", show_alert=True)
        return

    user_locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    try:
        # Получаем текущие цены
        prices = get_premium_prices()
        
        # Формируем текст с ценами
        text = "💵 Текущие цены:\n\n"
        
        duration_mapping = {
            30: "Месяц",
            180: "Полгода",
            365: "Год",
            36500: "Навсегда"
        }
        
        for price in prices:
            duration_name = duration_mapping.get(price.duration_days, f"{price.duration_days} дней")
            text += f"• {duration_name}: {price.price}₽\n"
        
        # Создаем клавиатуру для возврата
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"),
            callback_data="back_to_admin"
        ))
        
        await callback.message.edit_text(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка при получении цен: {str(e)}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=user_locale.get("back_to_admin_panel", "🔙 Назад в админ-панель"),
            callback_data="back_to_admin"
        ))
        await callback.message.edit_text(
            user_locale.get("error_loading_prices", "❌ Ошибка при загрузке цен"),
            reply_markup=kb
        )

def register_handlers_admin(dp: Dispatcher, locale):
    """Регистрирует обработчики админки"""
    dp.register_message_handler(lambda message: cmd_admin_panel(message, locale), commands=["admin", "panel"])
    
    # Обработчики для выдачи монет
    dp.register_callback_query_handler(
        lambda call, state: process_give_crystals(call, state, locale),
        lambda c: c.data == "give_crystals",
        state="*"
    )
    dp.register_message_handler(
        lambda message, state: process_user_id_for_crystals(message, state, locale),
        state=AdminGiveCrystalsStates.waiting_for_user_id
    )
    dp.register_message_handler(
        lambda message, state: process_crystals_amount(message, state, locale),
        state=AdminGiveCrystalsStates.waiting_for_amount
    )
    
    # Обработчики для премиума
    dp.register_callback_query_handler(
        lambda call, state: process_give_premium(call, state, locale),
        lambda c: c.data == "give_premium",
        state="*"
    )
    dp.register_message_handler(
        lambda message, state: process_user_id_input(message, state, locale),
        state=AdminStates.waiting_for_user_id
    )
    dp.register_callback_query_handler(
        lambda call, state: process_premium_duration(call, state, locale),
        lambda c: c.data.startswith("premium_"),
        state=AdminStates.waiting_for_duration
    )
    
    # Обработчики для цен
    dp.register_callback_query_handler(
        lambda call, state: process_admin_prices(call, state, locale),
        lambda c: c.data == "premium_prices",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_change_price(call, state, locale),
        lambda c: c.data.startswith("change_price:"),
        state="*"
    )
    dp.register_message_handler(
        lambda message, state: process_price_input(message, state, locale),
        state=AdminStates.waiting_for_price
    )
    
    # Обработчики для спонсоров
    dp.register_callback_query_handler(
        lambda call, state: process_manage_sponsors(call, state, locale),
        lambda c: c.data == "manage_sponsors",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_add_sponsor(call, state, locale),
        lambda c: c.data == "add_sponsor",
        state="*"
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
        lambda call, state: process_toggle_sponsor(call, state, locale),
        lambda c: c.data.startswith("toggle_sponsor:"),
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_delete_sponsor_confirm(call, state, locale),
        lambda c: c.data.startswith("delete_sponsor:"),
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_confirm_delete_sponsor(call, state, locale),
        lambda c: c.data.startswith("confirm_delete_sponsor:"),
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_cancel_delete_sponsor(call, state, locale),
        lambda c: c.data.startswith("cancel_delete_sponsor:"),
        state="*"
    )
    
    # Обработчики для промокодов
    dp.register_callback_query_handler(
        lambda call, state: process_manage_promo_codes(call, state, locale),
        lambda c: c.data == "manage_promo_codes",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_add_promo_code(call, state, locale),
        lambda c: c.data == "add_promo_code",
        state="*"
    )
    dp.register_message_handler(
        lambda message, state: process_promo_code_input(message, state, locale),
        state=AdminStates.waiting_for_promo_code
    )
    dp.register_callback_query_handler(
        lambda call, state: process_promo_duration_selection(call, state, locale),
        lambda c: c.data.startswith("promo_duration:"),
        state=AdminStates.waiting_for_promo_duration
    )
    dp.register_callback_query_handler(
        lambda call, state: process_promo_uses_selection(call, state, locale),
        lambda c: c.data.startswith("promo_uses:"),
        state=AdminStates.waiting_for_promo_uses
    )
    dp.register_callback_query_handler(
        lambda call, state: process_promo_expiry_selection(call, state, locale),
        lambda c: c.data.startswith("promo_expiry:"),
        state=AdminStates.waiting_for_promo_expiry
    )
    dp.register_callback_query_handler(
        lambda call, state: process_delete_promo(call, state, locale),
        lambda c: c.data.startswith("delete_promo:"),
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_activate_promo(call, state, locale),
        lambda c: c.data.startswith("activate_promo:"),
        state="*"
    )
    
    # Обработчик для выдачи цен
    dp.register_callback_query_handler(
        lambda call, state: process_give_price(call, state, locale),
        lambda c: c.data == "give_price",
        state="*"
    )
    
    # Обработчик для кнопки "Назад"
    dp.register_callback_query_handler(
        lambda call, state: process_back_to_admin(call, state, locale),
        lambda c: c.data == "back_to_admin" or c.data == "manage_promo_codes" or c.data == "manage_sponsors",
        state="*"
    )
    
    # Обработчик отмены для всех состояний админ-панели
    dp.register_message_handler(
        lambda message, state: process_cancel_premium(message, state, locale),
        lambda message: message.text.lower() in ["отмена", "🔙", "/cancel"],
        state=[
            AdminStates.waiting_for_user_id,
            AdminStates.waiting_for_duration,
            AdminStates.waiting_for_price,
            AdminStates.waiting_for_sponsor_name,
            AdminStates.waiting_for_sponsor_link,
            AdminStates.waiting_for_sponsor_channel_id,
            AdminStates.waiting_for_sponsor_reward,
            AdminStates.waiting_for_promo_code,
            AdminStates.waiting_for_promo_duration,
            AdminStates.waiting_for_promo_uses,
            AdminStates.waiting_for_promo_expiry,
            AdminGiveCrystalsStates.waiting_for_user_id,
            AdminGiveCrystalsStates.waiting_for_amount
        ]
    ) 