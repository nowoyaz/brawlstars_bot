from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import get_user_crystals, process_crystal_transfer
from keyboards.inline_keyboard import inline_main_menu_keyboard, cancel_keyboard

# FSM для отправки кристаллов
class SendCrystalsStates(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_amount = State()

# Обработчик показа меню кристаллов
async def cmd_crystals(callback: types.CallbackQuery, locale):
    await callback.answer()
    crystals = get_user_crystals(callback.from_user.id)
    user_id = callback.from_user.id
    # Выводим текст с моноширинным ID (Markdown)
    text = locale["crystals_text"].format(crystals=crystals, user_id=user_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
         types.InlineKeyboardButton(text=locale["button_send_crystals"], callback_data="send_crystals"),
         types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# Обработчик кнопки "Отправить кристаллы" – запускает FSM
async def process_send_crystals(callback: types.CallbackQuery, locale, state: FSMContext):
    await callback.answer()
    # Отправляем сообщение с запросом ID получателя, добавляем клавиатуру "Назад"
    await callback.message.edit_text(locale["prompt_recipient"], reply_markup=cancel_keyboard(locale))
    await SendCrystalsStates.waiting_for_recipient.set()

# Обработчик для отмены FSM (кнопка "Назад")
async def cancel_send_crystals(callback: types.CallbackQuery, locale):
    await callback.answer("Отменено")
    # Завершаем FSM и возвращаем в главное меню
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

# Обработчик для ввода ID получателя
async def process_recipient(message: types.Message, locale, state: FSMContext):
    recipient_text = message.text.strip()
    if not recipient_text.isdigit():
        await message.answer(locale["error_invalid_recipient"])
        return
    recipient_id = int(recipient_text)
    await state.update_data(recipient_id=recipient_id)
    # Запрашиваем количество кристаллов, добавляем клавиатуру "Назад"
    await message.answer(locale["prompt_amount"], reply_markup=cancel_keyboard(locale))
    await SendCrystalsStates.waiting_for_amount.set()

# Обработчик для ввода количества кристаллов
async def process_amount(message: types.Message, locale, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(locale["error_invalid_amount"])
        return
    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    sender_id = message.from_user.id
    sender_crystals = get_user_crystals(sender_id)
    if amount > sender_crystals:
        # Если недостаточно кристаллов, отправляем сообщение с кнопкой "Назад"
        await message.answer(locale["error_insufficient_crystals"].format(crystals=sender_crystals), reply_markup=cancel_keyboard(locale))
        return
    success, response = process_crystal_transfer(sender_id, recipient_id, amount)
    if success:
        await message.answer(locale["transfer_success"].format(amount=amount, recipient=recipient_id), reply_markup=inline_main_menu_keyboard(locale))
        # Уведомление получателю о переводе
        await message.bot.send_message(recipient_id, 
            f"✅ Вам пришло {amount} кристаллов от пользователя {sender_id}.")
    else:
        await message.answer(locale["transfer_error"].format(error=response), reply_markup=cancel_keyboard(locale))
    await state.finish()

# Обработчик для кнопки "Назад" из меню кристаллов
async def process_back_to_main(callback: types.CallbackQuery, locale):
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_crystals(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_crystals(call, locale), lambda c: c.data == "crystals")
    dp.register_callback_query_handler(lambda call, state: process_send_crystals(call, locale, state), lambda c: c.data == "send_crystals")
    dp.register_callback_query_handler(lambda call: cancel_send_crystals(call, locale), lambda c: c.data == "cancel_send_crystals")
    dp.register_callback_query_handler(lambda call: process_back_to_main(call, locale), lambda c: c.data == "back_to_main")
    dp.register_message_handler(lambda message, state: process_recipient(message, locale, state), state=SendCrystalsStates.waiting_for_recipient)
    dp.register_message_handler(lambda message, state: process_amount(message, locale, state), state=SendCrystalsStates.waiting_for_amount)
