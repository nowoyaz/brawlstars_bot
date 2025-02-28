from aiogram import types
from aiogram.dispatcher import Dispatcher
from config import ADMIN_ID
from keyboards.inline_keyboard import report_reason_keyboard, report_admin_keyboard

async def cmd_report(callback: types.CallbackQuery, locale):
    await callback.answer()
    text = locale["report_text"]
    await callback.message.edit_text(text, reply_markup=report_reason_keyboard(locale, 0, "default"))

async def process_report(callback: types.CallbackQuery, locale):
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

def register_handlers_report(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_report(call, locale), lambda c: c.data.startswith("report:default"))
    dp.register_callback_query_handler(lambda call: process_report(call, locale), lambda c: c.data.startswith("report:") and c.data != "report:default")
