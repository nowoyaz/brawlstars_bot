from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import get_user_crystals, process_crystal_transfer

async def cmd_crystals(callback: types.CallbackQuery, locale):
    await callback.answer()
    crystals = get_user_crystals(callback.from_user.id)
    text = locale["crystals_text"].format(crystals=crystals, user_id=callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=None)

async def cmd_send_crystals(message: types.Message, locale):
    args = message.text.split()
    if len(args) < 3:
        await message.answer(locale["send_crystals_usage"])
        return
    receiver_id = args[1]
    try:
        amount = int(args[2])
    except ValueError:
        await message.answer(locale["invalid_amount"])
        return
    success, response = process_crystal_transfer(message.from_user.id, receiver_id, amount)
    await message.answer(response)

def register_handlers_crystals(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_crystals(call, locale), lambda c: c.data == "crystals")
    dp.register_message_handler(lambda message: cmd_send_crystals(message, locale), commands=["send_crystals"])
