from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.reply_keyboard import main_menu_keyboard
from utils.helpers import get_user_language, record_section_visit

async def cmd_menu(message: types.Message, locale):
    locale = get_user_language(message.from_user.id)
    text = locale["menu_text"]
    await message.answer(text, reply_markup=main_menu_keyboard(locale))

def register_handlers_menu(dp: Dispatcher, locale):
    dp.register_message_handler(lambda message: cmd_menu(message, locale), text=locale["button_start"])
