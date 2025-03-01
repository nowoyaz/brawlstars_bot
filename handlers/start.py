from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline_keyboard import start_keyboard, inline_main_menu_keyboard

async def cmd_start(message: types.Message, locale, state: FSMContext):
    # Завершаем все активные состояния
    await state.finish()
    text = locale["start_text"]
    await message.answer(text, reply_markup=start_keyboard(locale))

async def process_start_callback(callback: types.CallbackQuery, locale):
    await callback.answer()
    text = locale["menu_text"]
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_start(dp: Dispatcher, locale):
    dp.register_message_handler(lambda message, state: cmd_start(message, locale, state), commands=["start"])
    dp.register_callback_query_handler(lambda call: process_start_callback(call, locale), lambda c: c.data == "menu")
