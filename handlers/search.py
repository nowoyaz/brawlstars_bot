from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from utils.helpers import (
    get_next_announcement,
    get_user_announcement,
    get_announcements_count,
    add_favorite,
    report_announcement,
    get_filtered_announcement,
    get_announcements_list,
    get_announcement_by_id,
    is_user_premium
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
    search_filters_keyboard,
    report_admin_keyboard,
    report_confirmation_keyboard
)
from config import ADMIN_ID
from utils.helpers import get_user_language

# ----- Меню поиска -----

async def process_search_team_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["search_team_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_team_menu_keyboard(locale))

async def process_search_club_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["search_club_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_club_menu_keyboard(locale))

# ----- "Мое объявление" -----

async def process_my_announcement(callback: types.CallbackQuery, locale, announcement_type: str):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Если пользователь не премиум, проверяем наличие объявления в другой категории
    from utils.helpers import is_user_premium
    if not is_user_premium(callback.from_user.id):
        opposite_type = "club" if announcement_type == "team" else "team"
        opposite = get_user_announcement(callback.from_user.id, opposite_type)
        if opposite:
            await callback.message.edit_text(f"Вы уже создали объявление в категории '{opposite_type}'.", reply_markup=inline_main_menu_keyboard(locale))
            return
    announcement = get_user_announcement(callback.from_user.id, announcement_type)
    if announcement:
        premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
        text = f"<b>Ваше объявление:</b>\n{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
        media = types.InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.edit_media(media, reply_markup=announcement_view_keyboard(locale))
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        kb.add(types.InlineKeyboardButton(text=locale["button_create_new"], callback_data=f"create_new_{announcement_type}"))
        await callback.message.edit_text(locale["no_announcement_create_prompt"], reply_markup=kb)

# ----- Обычный поиск чужого объявления -----

async def process_search_team_options(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["search_options_text"]
    await callback.message.edit_text(text, reply_markup=search_options_keyboard(locale))

async def process_search_club_options(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["search_options_text"]
    await callback.message.edit_text(text, reply_markup=search_options_club_keyboard(locale))

async def process_normal_search_team_confirmation(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="team"))

async def process_next_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement_list = get_announcements_list("team", callback.from_user.id)
    if not announcement_list:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    # Получаем текущий индекс из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    announcement_index = data.get("announcement_index", 0)
    count = len(announcement_list)
    # Обновляем индекс циклично
    next_index = (announcement_index + 1) % count
    await state.update_data(announcement_index=next_index)
    current_id = announcement_list[announcement_index]
    announcement = get_announcement_by_id(current_id)
    if announcement:
        text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
        has_next = count > 1
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "team")
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("team", callback.from_user.id)
    if announcement:
        count = get_announcements_count("team", callback.from_user.id)
        has_next = count > 1
        premium_label = " 💎 PREMIUM" if is_user_premium(announcement['user_id']) else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}\n{premium_label}"
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "team")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club_confirmation(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="club"))

async def process_next_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement_list = get_announcements_list("team", callback.from_user.id)
    if not announcement_list:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    # Получаем текущий индекс из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    announcement_index = data.get("announcement_index", 0)
    count = len(announcement_list)
    # Обновляем индекс циклично
    next_index = (announcement_index + 1) % count
    await state.update_data(announcement_index=next_index)
    current_id = announcement_list[announcement_index]
    announcement = get_announcement_by_id(current_id)
    if announcement:
        text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
        has_next = count > 1
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "team")
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_next_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement_list = get_announcements_list("club", callback.from_user.id)
    if not announcement_list:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    data = await state.get_data()
    announcement_index = data.get("announcement_index", 0)
    count = len(announcement_list)
    next_index = (announcement_index + 1) % count
    await state.update_data(announcement_index=next_index)
    current_id = announcement_list[announcement_index]
    announcement = get_announcement_by_id(current_id)
    if announcement:
        text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
        has_next = count > 1
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "club")
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}\n{premium_label}"

        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "club")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
# ----- Избранное -----

async def process_favorite(callback: types.CallbackQuery, locale, announcement_type: str):
    locale = get_user_language(callback.from_user.id)
    await callback.answer(locale["button_favorite"] + " ✅")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        add_favorite(callback.from_user.id, announcement_id)
    if announcement_type == "team":
        await process_normal_search_team(callback, locale)
    else:
        await process_normal_search_club(callback, locale)

# ----- Репорт -----

async def process_report_selection(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 4:
        announcement_id, reason, announcement_type = int(data[1]), data[2], data[3]
        confirm_text = "🤔 Вы уверены, что хотите пожаловаться на этого пользователя? При ложных репортах вы можете быть наказаны. ⚖️"
        # Если сообщение содержит фотографию, удаляем его и отправляем новое текстовое сообщение
        try:
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.bot.send_message(
                    callback.from_user.id,
                    confirm_text,
                    reply_markup=report_confirmation_keyboard(announcement_id, announcement_type, reason)
                )
            else:
                await callback.message.edit_text(
                    confirm_text,
                    reply_markup=report_confirmation_keyboard(announcement_id, announcement_type, reason)
                )
        except Exception:
            # На случай ошибок отправляем новое сообщение
            await callback.message.bot.send_message(
                callback.from_user.id,
                confirm_text,
                reply_markup=report_confirmation_keyboard(announcement_id, announcement_type, reason)
            )

async def confirm_report(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Ожидаемый формат: "confirm_report:<announcement_id>:<reason>:<announcement_type>:yes"
    data = callback.data.split(":")
    if len(data) >= 5:
        announcement_id, reason, announcement_type, confirmation = int(data[1]), data[2], data[3], data[4]
        if confirmation == "yes":
            report_announcement(callback.from_user.id, announcement_id, reason)
            from utils.helpers import get_announcement_by_id
            announcement = get_announcement_by_id(announcement_id)
            if announcement:
                text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}\nПричина: {reason}"
                await callback.bot.send_photo(
                    ADMIN_ID,
                    photo=announcement["image_id"],
                    caption=text,
                    reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
                )
        try:
            await callback.message.delete()
        except Exception:
            pass
        # Переход к следующему объявлению, если оно есть:
        if announcement_type == "team":
            next_ann = get_next_announcement("team", callback.from_user.id)
            if next_ann:
                await process_normal_search_team(callback, locale)
            else:
                await callback.message.bot.send_message(callback.from_user.id, "Список пуст", reply_markup=inline_main_menu_keyboard(locale))
        else:
            next_ann = get_next_announcement("club", callback.from_user.id)
            if next_ann:
                await process_normal_search_club(callback, locale)
            else:
                await callback.message.bot.send_message(callback.from_user.id, "Список пуст", reply_markup=inline_main_menu_keyboard(locale))

async def cancel_report(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer("Отменено")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        announcement_type = data[2]
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            count = get_announcements_count(announcement_type, callback.from_user.id)
            has_next = count > 1
            text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, announcement_type)
            )
        else:
            await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))


async def process_report(callback: types.CallbackQuery, locale, announcement_type: str):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        # Если сообщение содержит фото, пытаемся вызвать edit_caption, иначе edit_text
        try:
            await callback.message.edit_caption(locale["report_text"], reply_markup=report_reason_keyboard(locale, announcement_id, announcement_type))
        except Exception:
            await callback.message.edit_text(locale["report_text"], reply_markup=report_reason_keyboard(locale, announcement_id, announcement_type))

async def process_report_reason(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 4:
        announcement_id, reason, announcement_type = int(data[1]), data[2], data[3]
        # Сохраняем репорт с указанной причиной
        report_announcement(callback.from_user.id, announcement_id, reason)
        
        # Получаем данные репортованного объявления
        from utils.helpers import get_announcement_by_id
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
            # Отправляем админу фото с анкетой и клавиатурой для блокировки/игнорирования.
            # Передаём в report_admin_keyboard locale, announcement["user_id"] и callback.from_user.id
            await callback.bot.send_photo(
                ADMIN_ID,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
            )
        try:
            await callback.message.delete()
        except Exception:
            pass
        # Переходим к следующему объявлению, если оно есть
        if announcement_type == "team":
            next_ann = get_next_announcement("team", callback.from_user.id)
            if next_ann:
                await process_normal_search_team(callback, locale)
            else:
                await callback.message.bot.send_message(callback.from_user.id, "Список пуст", reply_markup=inline_main_menu_keyboard(locale))
        else:
            next_ann = get_next_announcement("club", callback.from_user.id)
            if next_ann:
                await process_normal_search_club(callback, locale)
            else:
                await callback.message.bot.send_message(callback.from_user.id, "Список пуст", reply_markup=inline_main_menu_keyboard(locale))

# ----- Фильтрация -----

async def process_filtered_search(callback: types.CallbackQuery, locale, announcement_type: str):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Ожидается, что callback.data имеет формат "filtered_search_<announcement_type>_<order>"
    data = callback.data.split("_")
    if len(data) >= 3:
        order = data[2]  # Например, "new", "old" или "premium"
        announcement_list = get_filtered_announcement(announcement_type, callback.from_user.id, order)
    else:
        announcement_list = []
    if announcement_list:
        from utils.helpers import get_announcement_by_id
        announcement = get_announcement_by_id(announcement_list[0])
        if announcement:
            premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
            text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}\n{premium_label}"
            # Если список содержит больше одного элемента, кнопка "Дальше" появится
            has_next = len(announcement_list) > 1
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, announcement_type)
            )
        else:
            await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))
    else:
        await callback.message.edit_text("Объявлений по выбранному фильтру нет 😕", reply_markup=inline_main_menu_keyboard(locale))


async def show_filters_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Показываем список фильтров для команды
    await callback.message.edit_text("Выберите фильтр для поиска команды:", reply_markup=search_filters_keyboard(locale, "team"))

async def show_filters_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Показываем список фильтров для клуба
    await callback.message.edit_text("Выберите фильтр для поиска клуба:", reply_markup=search_filters_keyboard(locale, "club"))







# ----- Кнопка "Назад" -----

async def process_back_to_search_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.delete()
    await callback.message.bot.send_message(callback.from_user.id, "Главное меню", reply_markup=inline_main_menu_keyboard(locale))


async def process_back_report(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        announcement_type = data[2]
        from utils.helpers import get_announcement_by_id
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            count = get_announcements_count(announcement_type, callback.from_user.id)
            has_next = count > 1
            text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}"
            await callback.message.delete()
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, announcement_type)
            )
        else:
            await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))
# ----- Регистрация обработчиков -----

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
    dp.register_callback_query_handler(lambda call: process_filtered_search(call, locale, "team"), lambda c: c.data.startswith("filtered_search_team"))
    dp.register_callback_query_handler(lambda call: process_filtered_search(call, locale, "club"), lambda c: c.data.startswith("filtered_search_club"))
    
    # Назад
    dp.register_callback_query_handler(lambda call: process_back_to_search_menu(call, locale), lambda c: c.data == "back_to_search_menu")
    dp.register_callback_query_handler(lambda call: process_back_report(call, locale), lambda c: c.data.startswith("back_report:"))
        

    dp.register_callback_query_handler(lambda call, state: process_next_team(call, locale, state), lambda c: c.data == "next:team")
    dp.register_callback_query_handler(lambda call, state: process_next_club(call, locale, state), lambda c: c.data == "next:club")
    
    dp.register_callback_query_handler(lambda call: show_filters_team(call, locale), lambda c: c.data == "show_filters_team")
    dp.register_callback_query_handler(lambda call: show_filters_club(call, locale), lambda c: c.data == "show_filters_club")


    dp.register_callback_query_handler(lambda call: process_report_selection(call, locale), lambda c: c.data.startswith("confirm_report_selection:"))
    dp.register_callback_query_handler(lambda call: confirm_report(call, locale), lambda c: c.data.startswith("confirm_report:"))
    dp.register_callback_query_handler(lambda call: cancel_report(call, locale), lambda c: c.data.startswith("cancel_report:"))
