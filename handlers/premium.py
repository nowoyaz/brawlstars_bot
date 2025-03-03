from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import process_premium_purchase, get_user_crystals, is_user_premium
from config import ADMIN_ID
from utils.helpers import get_user_language


async def cmd_premium(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    user_crystals = get_user_crystals(callback.from_user.id)
    premium_status = "🪙 Премиум активирован" if is_user_premium(callback.from_user.id) else ""
    text = locale["premium_text"].format(user_crystals) + "\n" + premium_status
    kb = types.InlineKeyboardMarkup(row_width=1)
    # Если пользователь не премиум, показываем кнопку "Купить"
    if not is_user_premium(callback.from_user.id):
        kb.add(types.InlineKeyboardButton(text=locale["button_buy_premium"], callback_data="buy_premium"))
    await callback.message.edit_text(text, reply_markup=kb)

async def cmd_buy_premium(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    user_crystals = get_user_crystals(callback.from_user.id)
    if user_crystals >= 500:
        process_premium_purchase(callback.from_user.id)
        await callback.message.edit_text(locale["premium_success"])
    else:
        await callback.message.edit_text(locale["premium_fail"].format(crystals=user_crystals))

def register_handlers_premium(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_premium(call, locale), lambda c: c.data == "premium")
    dp.register_callback_query_handler(lambda call: cmd_buy_premium(call, locale), lambda c: c.data == "buy_premium")
