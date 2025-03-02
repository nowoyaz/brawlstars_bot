from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from database.session import SessionLocal
from database.models import Announcement
from utils.helpers import (
    get_next_announcement,
    get_user_announcement,
    get_announcements_count,
    add_favorite,
    remove_favorite,
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
    report_confirmation_keyboard,
    keyword_filter_keyboard
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

async def process_unfavorite(callback: types.CallbackQuery, locale):
    """
    Обработчик удаления объявления из избранного
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer(locale["button_unfavorites"] + " ✅")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        remove_favorite(callback.from_user.id, announcement_id)
        # После удаления возвращаемся к списку избранного
        from handlers.favorites import process_favorites_menu
        await process_favorites_menu(callback, locale)

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

async def process_back_report(callback: types.CallbackQuery, locale):
    """
    Обработчик для кнопки "Назад" из меню репорта,
    возвращает пользователя к просмотру объявления
    """
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
            text = display_announcement_with_keyword(announcement, locale)
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
                # Используем форматирование с ключевыми словами для админа
                text = f"{display_announcement_with_keyword(announcement, locale)}\nПричина: {reason}"
                await callback.bot.send_photo(
                    ADMIN_ID,
                    photo=announcement["image_id"],
                    caption=text,
                    reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
                )
                
                # Сообщаем пользователю об успешной отправке репорта
                await callback.answer(locale.get("report_sent_success", "Репорт успешно отправлен"), show_alert=True)
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
                await callback.message.bot.send_message(callback.from_user.id, locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        else:
            next_ann = get_next_announcement("club", callback.from_user.id)
            if next_ann:
                await process_normal_search_club(callback, locale)
            else:
                await callback.message.bot.send_message(callback.from_user.id, locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

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
            # Используем функцию для отображения с ключевым словом
            text = display_announcement_with_keyword(announcement, locale)
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
    """
    Обрабатывает выбор причины репорта и отправляет репорт администратору
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Ожидаемый формат: "report_reason:<announcement_id>:<reason>:<announcement_type>"
    data = callback.data.split(":")
    if len(data) >= 4:
        announcement_id, reason, announcement_type = int(data[1]), data[2], data[3]
        
        # Сохраняем репорт с указанной причиной
        report_announcement(callback.from_user.id, announcement_id, reason)
        
        # Получаем данные репортованного объявления
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            # Формируем сообщение для админа
            text = f"{announcement['description']}\n\n🕒 {announcement['created_at']}\nПричина репорта: {reason}"
            
            try:
                # Отправляем админу фото с анкетой и клавиатурой для блокировки/игнорирования
                await callback.bot.send_photo(
                    ADMIN_ID,
                    photo=announcement["image_id"],
                    caption=text,
                    reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
                )
                
                # Отвечаем пользователю, что репорт отправлен
                await callback.answer("Ваш репорт успешно отправлен и будет рассмотрен", show_alert=True)
            except Exception as e:
                print(f"Ошибка при отправке репорта админу: {e}")
                await callback.answer("Произошла ошибка при отправке репорта", show_alert=True)
        
        try:
            # Удаляем сообщение с выбором причины репорта
            await callback.message.delete()
        except Exception:
            pass
        
        # Переходим к следующему объявлению, если оно есть
        if announcement_type == "team":
            next_ann = get_next_announcement("team", callback.from_user.id)
            if next_ann:
                await process_normal_search_team(callback, locale)
            else:
                await callback.message.bot.send_message(
                    callback.from_user.id, 
                    locale["no_announcements"], 
                    reply_markup=inline_main_menu_keyboard(locale)
                )
        else:
            next_ann = get_next_announcement("club", callback.from_user.id)
            if next_ann:
                await process_normal_search_club(callback, locale)
            else:
                await callback.message.bot.send_message(
                    callback.from_user.id, 
                    locale["no_announcements"], 
                    reply_markup=inline_main_menu_keyboard(locale)
                )

# ----- Фильтрация -----

async def process_filtered_search(callback: types.CallbackQuery, locale, announcement_type: str, order: str = "new"):
    """
    Обработчик для поиска объявлений с фильтрацией
    """
    locale = get_user_language(callback.from_user.id)
    announcements = get_filtered_announcement(announcement_type, callback.from_user.id, order)
    
    if not announcements:
        kb = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=kb)
        return
    
    # Берем первое объявление
    announcement = announcements[0]
    text = display_announcement_with_keyword(announcement, locale)
    
    # Проверяем, есть ли еще объявления
    has_next = len(announcements) > 1
    
    # Отправляем сообщение с объявлением
    await callback.message.delete()
    await callback.message.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=announcement["image_id"],
        caption=text,
        reply_markup=announcement_keyboard(
            locale,
            announcement["id"],
            announcement["user_id"],
            has_next,
            announcement_type
        )
    )

async def show_filters_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Добавляем кнопку для фильтрации по ключевым словам
    text = locale["filter_options_text"]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text="🆕 " + locale["filter_new"], callback_data="filter_new_team"),
        types.InlineKeyboardButton(text="🔄 " + locale["filter_old"], callback_data="filter_old_team"),
        types.InlineKeyboardButton(text="⭐ " + locale["filter_premium"], callback_data="filter_premium_team"),
        types.InlineKeyboardButton(text=locale["filter_by_keyword"], callback_data="filter_keyword_team")
    )
    kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_options_menu"))
    
    await callback.message.edit_text(text, reply_markup=kb)

async def show_filters_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Добавляем кнопку для фильтрации по ключевым словам
    text = locale["filter_options_text"]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text="🆕 " + locale["filter_new"], callback_data="filter_new_club"),
        types.InlineKeyboardButton(text="🔄 " + locale["filter_old"], callback_data="filter_old_club"),
        types.InlineKeyboardButton(text="⭐ " + locale["filter_premium"], callback_data="filter_premium_club"),
        types.InlineKeyboardButton(text=locale["filter_by_keyword"], callback_data="filter_keyword_club")
    )
    kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_options_menu"))
    
    await callback.message.edit_text(text, reply_markup=kb)

# ----- Кнопка "Назад" -----

async def process_back_to_search_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.delete()
    await callback.message.bot.send_message(callback.from_user.id, "Главное меню", reply_markup=inline_main_menu_keyboard(locale))


async def filter_keyword_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        locale["filter_by_keyword"],
        reply_markup=keyword_filter_keyboard(locale, "team")
    )

async def filter_keyword_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        locale["filter_by_keyword"],
        reply_markup=keyword_filter_keyboard(locale, "club")
    )

async def filter_by_keyword(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Извлекаем информацию из callback_data
    _, keyword, announcement_type = callback.data.split('_', 2)
    announcement_type = announcement_type.split('_')[-1]  # Извлекаем team или club
    
    # Получаем объявления с выбранным ключевым словом
    announcements = get_filtered_announcement(announcement_type, callback.from_user.id, "new", keyword)
    
    if not announcements:
        await callback.message.edit_text(
            locale["no_announcements"],
            reply_markup=search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        )
        return
    
    # Берем первое объявление из списка
    announcement = announcements[0]
    
    # Проверяем, есть ли еще объявления с этим фильтром
    has_next = len(announcements) > 1
    
    # Отправляем сообщение с фото
    await callback.message.delete()
    await callback.message.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=announcement["image_id"],
        caption=display_announcement_with_keyword(announcement, locale),
        reply_markup=announcement_keyboard(
            locale,
            announcement["id"],
            announcement["user_id"],
            has_next,
            announcement_type
        )
    )

def display_announcement_with_keyword(announcement, locale):
    # Функция для форматирования отображения объявления с ключевым словом
    keyword_text = ""
    if announcement.get("keyword"):
        keyword_display = locale.get(f"keyword_{announcement['keyword']}", announcement['keyword'])
        keyword_text = "\n" + locale["keyword_label"].format(keyword=keyword_display)
    
    premium_label = "⭐" if announcement.get("is_premium") else ""
    return f"{announcement['description']}{keyword_text}\n\n🕒 {announcement['created_at']}{premium_label}"

async def normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
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

async def normal_search_club(callback: types.CallbackQuery, locale):
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

async def my_announcement_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    announcement = get_user_announcement(callback.from_user.id, "team")
    if announcement:
        # Используем функцию для отображения с ключевым словом
        premium_label = "⭐" if is_user_premium(callback.from_user.id) else ""
        text = display_announcement_with_keyword(announcement, locale)
        
        # Создаем клавиатуру
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text=locale["button_delete"], callback_data=f"delete_announcement:{announcement['id']}:team"))
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        
        # Отправляем сообщение с объявлением и клавиатурой
        await callback.message.delete()
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=kb
        )
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=locale["button_create"], callback_data="create_new_team"))
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        await callback.message.edit_text(locale["no_announcement_create_prompt"], reply_markup=kb)

async def my_announcement_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    announcement = get_user_announcement(callback.from_user.id, "club")
    if announcement:
        # Используем функцию для отображения с ключевым словом
        premium_label = "⭐" if is_user_premium(callback.from_user.id) else ""
        text = display_announcement_with_keyword(announcement, locale)
        
        # Создаем клавиатуру
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text=locale["button_delete"], callback_data=f"delete_announcement:{announcement['id']}:club"))
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        
        # Отправляем сообщение с объявлением и клавиатурой
        await callback.message.delete()
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=kb
        )
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=locale["button_create"], callback_data="create_new_club"))
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        await callback.message.edit_text(locale["no_announcement_create_prompt"], reply_markup=kb)

async def process_back_to_main(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

async def process_back_to_search_options_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    if "team" in callback.data:
        await callback.message.edit_text(
            locale["search_options_text"], 
            reply_markup=search_options_keyboard(locale)
        )
    else:
        await callback.message.edit_text(
            locale["search_options_text"], 
            reply_markup=search_options_club_keyboard(locale)
        )

async def show_report_menu(callback: types.CallbackQuery, locale):
    """
    Функция для показа меню репорта.
    Алиас для process_report с определением типа объявления.
    """
    # Извлекаем данные из callback.data
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_type = data[2]
        # Вызываем основную функцию обработки репорта
        await process_report(callback, locale, announcement_type)

# ----- Регистрация обработчиков -----

def register_search_handlers(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: process_search_team_menu(call, locale), lambda c: c.data == "search_team_menu")
    dp.register_callback_query_handler(lambda call: process_search_club_menu(call, locale), lambda c: c.data == "search_club_menu")
    dp.register_callback_query_handler(lambda call: process_back_to_main(call, locale), lambda c: c.data == "back_to_main")
    dp.register_callback_query_handler(lambda call: process_back_to_search_menu(call, locale), lambda c: c.data.startswith("back_to_search_menu"))
    dp.register_callback_query_handler(lambda call: process_search_team_options(call, locale), lambda c: c.data == "search_team_search")
    dp.register_callback_query_handler(lambda call: process_search_club_options(call, locale), lambda c: c.data == "search_club_search")
    dp.register_callback_query_handler(lambda call: process_back_to_search_options_menu(call, locale), lambda c: c.data == "back_to_search_options_menu")
    
    # Регистрация для фильтров
    dp.register_callback_query_handler(
        lambda call, state: show_filters_team(call, locale, state),
        lambda c: c.data == "show_filters_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: show_filters_club(call, locale, state),
        lambda c: c.data == "show_filters_club",
        state="*"
    )
    
    # Регистрация для нормального поиска
    dp.register_callback_query_handler(
        lambda call, state: normal_search_team(call, locale, state),
        lambda c: c.data == "normal_search_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: normal_search_club(call, locale, state),
        lambda c: c.data == "normal_search_club",
        state="*"
    )
    
    # Регистрация для просмотра своих объявлений
    dp.register_callback_query_handler(
        lambda call, state: my_announcement_team(call, locale, state),
        lambda c: c.data == "my_announcement_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: my_announcement_club(call, locale, state),
        lambda c: c.data == "my_announcement_club",
        state="*"
    )
    
    # Добавим новые обработчики для фильтрации по ключевым словам
    dp.register_callback_query_handler(
        lambda call, state: filter_keyword_team(call, locale, state),
        lambda c: c.data == "filter_keyword_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_keyword_club(call, locale, state),
        lambda c: c.data == "filter_keyword_club",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_by_keyword(call, locale, state),
        lambda c: c.data.startswith("filter_keyword_") and not c.data in ["filter_keyword_team", "filter_keyword_club"],
        state="*"
    )
    
    # Исправленные регистрации для избранного, репортов и прочих функций
    dp.register_callback_query_handler(lambda call: process_favorite(call, locale, "team"), lambda c: c.data.startswith("favorite:") and ":team" in c.data)
    dp.register_callback_query_handler(lambda call: process_favorite(call, locale, "club"), lambda c: c.data.startswith("favorite:") and ":club" in c.data)
    dp.register_callback_query_handler(lambda call: process_unfavorite(call, locale), lambda c: c.data.startswith("unfavorite:"))
    dp.register_callback_query_handler(lambda call: process_back_report(call, locale), lambda c: c.data.startswith("back_report:"))
    dp.register_callback_query_handler(lambda call: process_report_reason(call, locale), lambda c: c.data.startswith("report_reason:"))
    dp.register_callback_query_handler(lambda call: process_report_selection(call, locale), lambda c: c.data.startswith("confirm_report_selection:"))
    
    dp.register_callback_query_handler(lambda call: delete_announcement(call, locale), lambda c: c.data.startswith("delete_announcement:"))
    dp.register_callback_query_handler(lambda call: confirm_normal_search_team(call, locale), lambda c: c.data == "confirm_normal_search_team")
    dp.register_callback_query_handler(lambda call: confirm_normal_search_club(call, locale), lambda c: c.data == "confirm_normal_search_club")
    dp.register_callback_query_handler(lambda call: get_next_team(call, locale), lambda c: c.data.startswith("next_team"))
    dp.register_callback_query_handler(lambda call: get_next_club(call, locale), lambda c: c.data.startswith("next_club"))
    dp.register_callback_query_handler(lambda call: filter_new_team(call, locale), lambda c: c.data == "filter_new_team")
    dp.register_callback_query_handler(lambda call: filter_old_team(call, locale), lambda c: c.data == "filter_old_team")
    dp.register_callback_query_handler(lambda call: filter_premium_team(call, locale), lambda c: c.data == "filter_premium_team")
    dp.register_callback_query_handler(lambda call: filter_new_club(call, locale), lambda c: c.data == "filter_new_club")
    dp.register_callback_query_handler(lambda call: filter_old_club(call, locale), lambda c: c.data == "filter_old_club")
    dp.register_callback_query_handler(lambda call: filter_premium_club(call, locale), lambda c: c.data == "filter_premium_club")
    dp.register_callback_query_handler(lambda call: write_to_owner(call, locale), lambda c: c.data.startswith("write:"))
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "team"), lambda c: c.data.startswith("report:") and ":team" in c.data)
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "club"), lambda c: c.data.startswith("report:") and ":club" in c.data)
    dp.register_callback_query_handler(lambda call: process_report_reason(call, locale), lambda c: c.data.startswith("report_reason:"))
    dp.register_callback_query_handler(lambda call: confirm_report(call, locale), lambda c: c.data.startswith("confirm_report:"))
    dp.register_callback_query_handler(lambda call: cancel_report(call, locale), lambda c: c.data.startswith("cancel_report:"))

async def get_next_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("team", callback.from_user.id)
    if announcement:
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        # Проверяем, есть ли больше одного объявления
        count = get_announcements_count("team", callback.from_user.id)
        has_next = count > 1
        
        await callback.message.delete()
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(
                locale,
                announcement["id"],
                announcement["user_id"],
                has_next,
                "team"
            )
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=search_options_keyboard(locale))

async def get_next_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        # Проверяем, есть ли больше одного объявления
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        
        await callback.message.delete()
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(
                locale,
                announcement["id"],
                announcement["user_id"],
                has_next,
                "club"
            )
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=search_options_club_keyboard(locale))

async def filter_new_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "new")

async def filter_old_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "old")

async def filter_premium_team(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "premium")

async def filter_new_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "new")

async def filter_old_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "old")

async def filter_premium_club(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "premium")

async def delete_announcement(callback: types.CallbackQuery, locale):
    # Получаем данные из callback
    data = callback.data.split(":")
    announcement_id = int(data[1])
    announcement_type = data[2]
    
    # Получаем текущего пользователя
    user_id = callback.from_user.id
    
    # Открываем сессию базы данных
    session = SessionLocal()
    
    try:
        # Находим объявление
        announcement = session.query(Announcement).filter(Announcement.id == announcement_id).first()
        
        # Проверяем, принадлежит ли объявление пользователю
        if announcement and announcement.user_id == user_id:
            # Удаляем объявление
            session.delete(announcement)
            session.commit()
            
            # Отвечаем пользователю
            await callback.answer(locale["announcement_deleted"], show_alert=True)
            
            # Редактируем сообщение
            if announcement_type == "team":
                await callback.message.edit_text(
                    locale["search_team_menu_text"],
                    reply_markup=search_team_menu_keyboard(locale)
                )
            else:
                await callback.message.edit_text(
                    locale["search_club_menu_text"],
                    reply_markup=search_club_menu_keyboard(locale)
                )
        else:
            # Если объявление не найдено или не принадлежит пользователю
            await callback.answer(locale["not_your_announcement"], show_alert=True)
    except Exception as e:
        print(f"Error deleting announcement: {e}")
        await callback.answer(locale["error_deleting_announcement"], show_alert=True)
    finally:
        session.close()

async def write_to_owner(callback: types.CallbackQuery, locale):
    """
    Обработчик для кнопки "Написать"
    Так как эта кнопка уже содержит URL, этот обработчик не вызывается
    и сохранен только для совместимости
    """
    await callback.answer()

async def confirm_normal_search_team(callback: types.CallbackQuery, locale):
    """
    Подтверждение перехода к обычному поиску команды
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_team(callback, locale)
    
async def confirm_normal_search_club(callback: types.CallbackQuery, locale):
    """
    Подтверждение перехода к обычному поиску клуба
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_club(callback, locale)
