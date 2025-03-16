from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import get_user_crystals, get_user_language, process_crystal_transfer, record_section_visit, check_coins_achievement
from keyboards.inline_keyboard import inline_main_menu_keyboard
from database.crud import get_user_coins

async def cmd_crystals(callback: types.CallbackQuery, locale):
    """Обработчик для кнопки 'Монеты' - показывает баланс и позволяет отправить монеты"""
    locale = get_user_language(callback.from_user.id)
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "crystals")
    
    # Проверяем достижение "Лепрекон"
    check_coins_achievement(callback.from_user.id)
    
    # Получаем данные о пользователе
    from database.session import SessionLocal
    from database.models import User
    await callback.answer()
    session = SessionLocal()
    user = session.query(User).filter(User.tg_id == callback.from_user.id).first()
    coins = user.coins if user else 0
    session.close()
    
    text = locale["crystals_text"].format(crystals=coins, user_id=callback.from_user.id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

async def process_back_to_main(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_crystals(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_crystals(call, locale), lambda c: c.data == "crystals")
    dp.register_callback_query_handler(lambda call: process_back_to_main(call, locale), lambda c: c.data == "back_to_main")
