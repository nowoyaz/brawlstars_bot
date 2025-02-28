from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import (
    get_next_announcement,
    get_user_announcement,
    get_announcements_count,
    add_favorite,
    report_announcement
)
from keyboards.inline_keyboard import (
    search_team_menu_keyboard,
    search_options_keyboard,
    search_club_menu_keyboard,
    search_options_club_keyboard,
    confirmation_keyboard,
    announcement_keyboard,
    inline_main_menu_keyboard,
    announcement_view_keyboard,
    report_reason_keyboard,
    search_filters_keyboard
)
from config import ADMIN_ID

# ---------- Обработка меню поиска ----------

async def process_search_team_menu(callback: types.CallbackQuery, locale):
    """Обработка кнопки 'Поиск команды' – вывод меню поиска для команды."""
    await callback.answer()
    text = locale["search_team_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_team_menu_keyboard(locale))

async def process_search_club_menu(callback: types.CallbackQuery, locale):
    """Обработка кнопки 'Поиск клуба' – вывод меню поиска для клуба."""
    await callback.answer()
    text = locale["search_club_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_club_menu_keyboard(locale))

# ---------- Отображение 'Моего объявления' ----------

async def process_my_announcement(callback: types.CallbackQuery, locale, announcement_type: str):
    """Показывает объявление пользователя (если есть) или предлагает создать новое."""
    await callback.answer()
    announcement = get_user_announcement(callback.from_user.id, announcement_type)
    if announcement:
        text = f"<b>Ваше объявление:</b>\n{announcement['description']}\n\n🕒 {announcement['created_at']}"
        media = types.InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.edit_media(media, reply_markup=announcement_view_keyboard(locale))
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        kb.add(types.InlineKeyboardButton(text=locale["button_create_new"], callback_data=f"create_new_{announcement_type}"))
        await callback.message.edit_text(locale["no_announcement_create_prompt"], reply_markup=kb)

# ---------- Обычный поиск чужого объявления ----------

async def process_search_team_options(callback: types.CallbackQuery, locale):
    """Обработка опций поиска команды (Обычный, с фильтрами, назад)."""
    await callback.answer()
    text = locale["search_options_text"]
    await callback.message.edit_text(text, reply_markup=search_options_keyboard(locale))

async def process_search_club_options(callback: types.CallbackQuery, locale):
    """Обработка опций поиска клуба (Обычный, с фильтрами, назад)."""
    await callback.answer()
    text = locale["search_options_text"]
    await callback.message.edit_text(text, reply_markup=search_options_club_keyboard(locale))

async def process_normal_search_team_confirmation(callback: types.CallbackQuery, locale):
    """Вывод совета для обычного поиска команды с кнопкой 'хорошо'."""
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="team"))

async def process_normal_search_team(callback: types.CallbackQuery, locale):
    """После подтверждения – показывает чужое объявление команды."""
    await callback.answer()
    announcement = get_next_announcement("team", callback.from_user.id)
    if announcement:
        count = get_announcements_count("team", callback.from_user.id)
        has_next = count > 1
        text = f"<b>{announcement['description']}</b>\n\n🕒 {announcement['created_at']}"
        await callback.message.edit_media(
            types.InputMediaPhoto(announcement["image_id"], caption=text),
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "team")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club_confirmation(callback: types.CallbackQuery, locale):
    """Вывод совета для обычного поиска клуба с кнопкой 'хорошо'."""
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="club"))

async def process_normal_search_club(callback: types.CallbackQuery, locale):
    """После подтверждения – показывает чужое объявление клуба."""
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        text = f"<b>{announcement['description']}</b>\n\n🕒 {announcement['created_at']}"
        await callback.message.edit_media(
            types.InputMediaPhoto(announcement["image_id"], caption=text),
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "club")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

# ---------- Избранное и Репорт ----------

async def process_favorite(callback: types.CallbackQuery, locale, announcement_type: str):
    await callback.answer(locale["button_favorite"] + " ✅")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        add_favorite(callback.from_user.id, announcement_id)
    if announcement_type == "team":
        await process_normal_search_team(callback, locale)
    else:
        await process_normal_search_club(callback, locale)

async def process_report(callback: types.CallbackQuery, locale, announcement_type: str):
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        await callback.message.edit_text(locale["report_text"], reply_markup=report_reason_keyboard(locale, announcement_id, announcement_type))

async def process_report_reason(callback: types.CallbackQuery, locale):
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 4:
        announcement_id, reason, announcement_type = int(data[1]), data[2], data[3]
        report_announcement(callback.from_user.id, announcement_id)
        report_text = (
            f"🚨 <b>Новый репорт!</b>\n"
            f"Пользователь: <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a>\n"
            f"🔹 Причина: {reason}\n"
            f"📌 Объявление ID: {announcement_id}"
        )
        await callback.bot.send_message(ADMIN_ID, report_text, parse_mode="HTML")
        if announcement_type == "team":
            await process_normal_search_team(callback, locale)
        else:
            await process_normal_search_club(callback, locale)

# ---------- Фильтрация поиска ----------

async def process_filtered_search(callback: types.CallbackQuery, locale, announcement_type: str):
    await callback.answer()
    await callback.message.edit_text("Выберите фильтр поиска:", reply_markup=search_filters_keyboard(locale, announcement_type))

# ---------- Кнопка "Назад" ----------

async def process_back_to_search_menu(callback: types.CallbackQuery, locale):
    await callback.answer()
    await callback.message.delete()
    await callback.message.bot.send_message(callback.from_user.id, "Главное меню", reply_markup=inline_main_menu_keyboard(locale))

# ---------- Регистрация обработчиков ----------

def register_handlers_search(dp: Dispatcher, locale):
    # Поиск команды
    dp.register_callback_query_handler(lambda call: process_search_team_menu(call, locale), lambda c: c.data == "search_team_menu")
    dp.register_callback_query_handler(lambda call: process_search_team_options(call, locale), lambda c: c.data == "search_team_search")
    dp.register_callback_query_handler(lambda call: process_normal_search_team_confirmation(call, locale), lambda c: c.data == "normal_search_team")
    dp.register_callback_query_handler(lambda call: process_normal_search_team(call, locale), lambda c: c.data == "confirm_normal_search_team")
    
    # Поиск клуба
    dp.register_callback_query_handler(lambda call: process_search_club_menu(call, locale), lambda c: c.data == "search_club_menu")
    dp.register_callback_query_handler(lambda call: process_search_club_options(call, locale), lambda c: c.data == "search_club_search")
    dp.register_callback_query_handler(lambda call: process_normal_search_club_confirmation(call, locale), lambda c: c.data == "normal_search_club")
    dp.register_callback_query_handler(lambda call: process_normal_search_club(call, locale), lambda c: c.data == "confirm_normal_search_club")
    
    # Моё объявление
    dp.register_callback_query_handler(lambda call: process_my_announcement(call, locale, "team"), lambda c: c.data == "my_announcement_team")
    dp.register_callback_query_handler(lambda call: process_my_announcement(call, locale, "club"), lambda c: c.data == "my_announcement_club")
    
    # Избранное
    dp.register_callback_query_handler(lambda call: process_favorite(call, locale, "team"), lambda c: c.data.startswith("favorite:") and "team" in c.data)
    dp.register_callback_query_handler(lambda call: process_favorite(call, locale, "club"), lambda c: c.data.startswith("favorite:") and "club" in c.data)
    
    # Репорт
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "team"), lambda c: c.data.startswith("report:") and "team" in c.data)
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "club"), lambda c: c.data.startswith("report:") and "club" in c.data)
    dp.register_callback_query_handler(lambda call: process_report_reason(call, locale), lambda c: c.data.startswith("report_reason:"))
    
    # Фильтрация
    dp.register_callback_query_handler(lambda call: process_filtered_search(call, locale, "team"), lambda c: c.data == "filtered_search_team")
    dp.register_callback_query_handler(lambda call: process_filtered_search(call, locale, "club"), lambda c: c.data == "filtered_search_club")
    
    # Назад
    dp.register_callback_query_handler(lambda call: process_back_to_search_menu(call, locale), lambda c: c.data == "back_to_search_menu")
