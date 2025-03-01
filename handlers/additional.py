from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.inline_keyboard import additional_keyboard, inline_main_menu_keyboard
from utils.helpers import get_user_announcements_count, get_referral_count
from utils.helpers import get_user_language

# Обработчик для раздела "Дополнительно"
async def cmd_additional(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["additional_text"]
    kb = additional_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)



async def process_announcement_count(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    team_count = get_user_announcements_count(callback.from_user.id, "team")
    club_count = get_user_announcements_count(callback.from_user.id, "club")
    total = team_count + club_count
    text = locale["announcement_count_text"].format(team=team_count, club=club_count, total=total)
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))



async def process_referral_program(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Формируем реферальную ссылку (замените YourBotUsername на имя вашего бота)
    referral_link = f"https://t.me/obrientest_bot?start={callback.from_user.id}"
    count = get_referral_count(callback.from_user.id)
    text = locale["referral_text"].format(referral_link=referral_link, count=count)
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))


# Обработчик для кнопки "Назад" – возвращает в главное меню
async def process_additional_back(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_handlers_additional(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_additional(call, locale), lambda c: c.data == "additional")
    dp.register_callback_query_handler(lambda call: process_announcement_count(call, locale), lambda c: c.data == "announcement_count")
    dp.register_callback_query_handler(lambda call: process_referral_program(call, locale), lambda c: c.data == "referral")
    dp.register_callback_query_handler(lambda call: process_additional_back(call, locale), lambda c: c.data == "back_to_main")
