from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import process_premium_purchase, check_user_crystals, get_user_crystals
from config import ADMIN_ID

async def cmd_premium(callback: types.CallbackQuery, locale):
    await callback.answer()
    text = locale["premium_text"].format(get_user_crystals(callback.from_user.id))
    await callback.message.edit_text(text, reply_markup=None)

async def cmd_buy_premium(callback: types.CallbackQuery, locale):
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
