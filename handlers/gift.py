import random
import datetime
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import inline_main_menu_keyboard, gift_keyboard
from utils.helpers import get_user_language

async def cmd_gift(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["gift_text"]
    kb = gift_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)

async def process_receive_gift(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    # Проверяем, прошло ли 2 часа с последнего подарка
    session = SessionLocal()
    user = session.query(User).filter(User.id == callback.from_user.id).first()
    now = datetime.datetime.utcnow()
    if user.last_gift is not None:
        diff = now - user.last_gift
        if diff < datetime.timedelta(hours=2):
            remaining = datetime.timedelta(hours=2) - diff
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            session.close()
            # Отправляем всплывающее уведомление с информацией об оставшемся времени
            await callback.answer(locale["gift_time_error"].format(minutes=minutes, seconds=seconds), show_alert=True)
            return
    # Если прошло достаточно времени, начисляем подарок
    gift_amount = random.randint(1, 10)
    user.crystals += gift_amount
    user.last_gift = now
    session.commit()
    session.close()
    # Отправляем всплывающее уведомление о получении подарка
    await callback.answer(locale["gift_success"].format(amount=gift_amount), show_alert=True)
    # Возвращаем пользователя в главное меню
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

async def process_gift_back(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_gift(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_gift(call, locale), lambda c: c.data == "gift")
    dp.register_callback_query_handler(lambda call: process_receive_gift(call, locale), lambda c: c.data == "receive_gift")
    dp.register_callback_query_handler(lambda call: process_gift_back(call, locale), lambda c: c.data == "back_to_main")
