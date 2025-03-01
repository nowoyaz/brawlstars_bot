from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import process_premium_purchase, get_user_crystals
# Для данного примера предполагается, что функция process_premium_purchase обновляет премиум статус и списывает 500 кристаллов

async def cmd_premium(callback: types.CallbackQuery, locale):
    await callback.answer()
    user_crystals = get_user_crystals(callback.from_user.id)
    # Форматируем текст премиума с количеством кристаллов пользователя
    text = locale["premium_text"].format(user_crystals)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text=locale["button_buy_premium"], callback_data="buy_premium"))
    await callback.message.edit_text(text, reply_markup=kb)

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
