from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.reply_keyboard import main_menu_keyboard

async def cmd_menu(message: types.Message, locale):
    text = locale["menu_text"]
    await message.answer(text, reply_markup=main_menu_keyboard(locale))

def register_handlers_menu(dp: Dispatcher, locale):
    dp.register_message_handler(lambda message: cmd_menu(message, locale), text=locale["button_start"])
