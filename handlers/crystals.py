from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import get_user_crystals, get_user_language
from keyboards.inline_keyboard import inline_main_menu_keyboard

async def cmd_crystals(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    crystals = get_user_crystals(callback.from_user.id)
    user_id = callback.from_user.id
    text = locale["crystals_text"].format(crystals=crystals, user_id=user_id)
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
