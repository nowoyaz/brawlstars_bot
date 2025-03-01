from aiogram import types
from aiogram.dispatcher import Dispatcher
from config import ADMIN_ID
from keyboards.inline_keyboard import report_reason_keyboard, report_admin_keyboard
from database.session import SessionLocal
from database.models import User
from utils.helpers import get_user_language


async def cmd_report(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["report_text"]
    await callback.message.edit_text(text, reply_markup=report_reason_keyboard(locale, 0, "default"))

async def process_report(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    reason = callback.data.split(":", 1)[1]
    report_message = (
        f"🚨 <b>Новый репорт!</b>\n"
        f"Пользователь: <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a>\n"
        f"Причина: {reason}\n"
        f"Объявление ID: {callback.message.message_id}"
    )
    await callback.bot.send_message(ADMIN_ID, report_message, reply_markup=report_admin_keyboard(locale))
    await callback.message.edit_text("Репорт отправлен! ✅")


async def admin_block(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer("Пользователь заблокирован")
    data = callback.data.split(":")
    if len(data) >= 2:
        reported_user_id = int(data[1])
        session = SessionLocal()
        user = session.query(User).filter(User.id == reported_user_id).first()
        if user:
            user.blocked = True
            session.commit()
        session.close()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.bot.send_message(ADMIN_ID, "Пользователь заблокирован.", reply_markup=None)

async def admin_block_reporter(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer("Репортировавший заблокирован")
    data = callback.data.split(":")
    if len(data) >= 2:
        reporter_id = int(data[1])
        session = SessionLocal()
        user = session.query(User).filter(User.id == reporter_id).first()
        if user:
            user.blocked = True
            session.commit()
        session.close()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.bot.send_message(ADMIN_ID, "Репортировавший заблокирован.", reply_markup=None)

async def admin_ignore(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer("Игнорировано")
    try:
        await callback.message.delete()
    except Exception:
        pass


def register_handlers_report(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_report(call, locale), lambda c: c.data.startswith("report:default"))
    dp.register_callback_query_handler(lambda call: process_report(call, locale), lambda c: c.data.startswith("report:") and c.data != "report:default")
    dp.register_callback_query_handler(lambda call: admin_block(call, locale), lambda c: c.data.startswith("admin_block"))
    dp.register_callback_query_handler(lambda call: admin_block_reporter(call, locale), lambda c: c.data.startswith("admin_block_reporter:"))
    dp.register_callback_query_handler(lambda call: admin_ignore(call, locale), lambda c: c.data.startswith("admin_ignore"))
