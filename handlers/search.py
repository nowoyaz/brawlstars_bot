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
    is_user_premium,
    get_paginated_announcements
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
        text = display_announcement_with_keyword(announcement, locale)
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

async def process_normal_search_team_confirmation(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_team(callback, locale, state)

async def process_next_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    next_page = current_page + 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("team", callback.from_user.id, next_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "team"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_prev_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    prev_page = current_page - 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("team", callback.from_user.id, prev_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "team"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Обработчик для перехода к просмотру обычных объявлений поиска команды
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Сбрасываем индекс просмотра на 0 при первом просмотре
    await state.update_data(announcement_page=0)
    # Сначала советуем использовать репорт
    await callback.message.edit_text(locale["normal_search_advice_text"], reply_markup=confirmation_keyboard(locale, "team"))

async def process_normal_search_club_confirmation(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="club"))

async def process_next_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    next_page = current_page + 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("club", callback.from_user.id, next_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "club"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_prev_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    prev_page = current_page - 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("club", callback.from_user.id, prev_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "club"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        premium_label = " 💎 PREMIUM" if is_user_premium(announcement['user_id']) else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

# ----- Избранное -----

async def process_favorite(callback: types.CallbackQuery, locale, announcement_type: str, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer(locale["button_favorite"] + " ✅")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        add_favorite(callback.from_user.id, announcement_id)
        
        # Получаем данные объявления для отображения
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            count = get_announcements_count(announcement_type, callback.from_user.id)
            has_next = count > 1
            has_prev = False  # На первой странице нет кнопки "назад"
            
            # Показываем объявление с отметкой премиум если нужно
            text = display_announcement_with_keyword(announcement, locale)
            
            try:
                await callback.message.delete()
            except Exception:
                pass
                
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
            )
        else:
            # Если объявление не найдено (маловероятно), просто вернемся к списку
            if announcement_type == "team":
                await process_search_team_menu(callback, locale)
            else:
                await process_search_club_menu(callback, locale)

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
            has_prev = False  # При возврате из меню репорта показываем первое объявление
            text = display_announcement_with_keyword(announcement, locale)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
            )
        else:
            await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def confirm_report(callback: types.CallbackQuery, locale):
    """
    Обработчик подтверждения репорта
    """
    locale = get_user_language(callback.from_user.id)
    data = callback.data.split(":")
    if len(data) >= 5:
        announcement_id = int(data[1])
        reason = data[2]
        announcement_type = data[3]
        confirmed = data[4]
        
        if confirmed == "yes":
            # Записываем репорт в базу данных
            report_announcement(callback.from_user.id, announcement_id, reason)
            await callback.answer(locale["button_report"] + " ✅")
            
            # Здесь можно добавить логику отправки уведомления администратору
            
            # Показываем следующее объявление
            if announcement_type == "team":
                announcement = get_next_announcement("team", callback.from_user.id)
                if announcement:
                    count = get_announcements_count("team", callback.from_user.id)
                    has_next = count > 1
                    has_prev = False  # Для упрощения, после репорта всегда показываем первое объявление
                    premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
                    text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
                    # Отправляем сообщение с фотографией
                    await callback.message.edit_media(
                        types.InputMediaPhoto(
                            media=announcement["image_id"],
                            caption=text
                        ),
                        reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                    )
                else:
                    await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
            elif announcement_type == "club":
                announcement = get_next_announcement("club", callback.from_user.id)
                if announcement:
                    count = get_announcements_count("club", callback.from_user.id)
                    has_next = count > 1
                    has_prev = False  # Для упрощения, после репорта всегда показываем первое объявление
                    premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
                    text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
                    # Отправляем сообщение с фотографией
                    await callback.message.edit_media(
                        types.InputMediaPhoto(
                            media=announcement["image_id"],
                            caption=text
                        ),
                        reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                    )
                else:
                    await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        else:
            await callback.answer("Репорт отменен")
    else:
        # Неверный формат данных
        await callback.answer("Ошибка в формате данных")

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
            has_prev = False  # После отмены репорта возвращаем первое объявление
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
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
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

async def process_filtered_search(callback: types.CallbackQuery, locale, announcement_type: str, order: str = "new", state: FSMContext = None):
    """
    Обработчик для поиска объявлений с фильтрацией
    """
    locale = get_user_language(callback.from_user.id)
    announcement_ids = get_filtered_announcement(announcement_type, callback.from_user.id, order)
    
    if not announcement_ids:
        kb = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=kb)
        return
    
    # Берем первое объявление
    announcement_id = announcement_ids[0]
    # Получаем полные данные объявления по ID
    announcement = get_announcement_by_id(announcement_id)
    
    if not announcement:
        kb = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=kb)
        return
        
    text = display_announcement_with_keyword(announcement, locale)
    
    # Проверяем, есть ли еще объявления
    has_next = len(announcement_ids) > 1
    has_prev = False  # На первой странице нет кнопки "назад"
    
    # Сохраняем данные в состоянии (если передан state)
    if state:
        await state.update_data(
            announcement_ids=announcement_ids,
            current_index=0,
            filter_order=order,
            announcement_type=announcement_type
        )
    
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
            has_prev,
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
    is_user_premium,
    get_paginated_announcements
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
        text = display_announcement_with_keyword(announcement, locale)
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

async def process_normal_search_team_confirmation(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_team(callback, locale, state)

async def process_next_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    next_page = current_page + 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("team", callback.from_user.id, next_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "team"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_prev_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    prev_page = current_page - 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("team", callback.from_user.id, prev_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "team"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Обработчик для перехода к просмотру обычных объявлений поиска команды
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Сбрасываем индекс просмотра на 0 при первом просмотре
    await state.update_data(announcement_page=0)
    # Сначала советуем использовать репорт
    await callback.message.edit_text(locale["normal_search_advice_text"], reply_markup=confirmation_keyboard(locale, "team"))

async def process_normal_search_club_confirmation(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="club"))

async def process_next_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM (если нет, начинаем с 0)
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    next_page = current_page + 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("club", callback.from_user.id, next_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "club"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_prev_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущую страницу из FSM
    data = await state.get_data()
    current_page = data.get("announcement_page", 0)
    prev_page = current_page - 1
    
    # Получаем объявления с пагинацией
    paginated_data = get_paginated_announcements("club", callback.from_user.id, prev_page)
    
    if not paginated_data["current_announcement"]:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        return
    
    # Сохраняем новую страницу в FSM
    await state.update_data(announcement_page=paginated_data["current_page"])
    
    announcement = paginated_data["current_announcement"]
    if announcement:
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
            reply_markup=announcement_keyboard(
                locale, 
                announcement["id"], 
                announcement["user_id"], 
                paginated_data["has_next"], 
                paginated_data["has_prev"],
                "club"
            )
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        premium_label = " 💎 PREMIUM" if is_user_premium(announcement['user_id']) else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

# ----- Избранное -----

async def process_favorite(callback: types.CallbackQuery, locale, announcement_type: str, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer(locale["button_favorite"] + " ✅")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        add_favorite(callback.from_user.id, announcement_id)
        
        # Получаем данные объявления для отображения
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            count = get_announcements_count(announcement_type, callback.from_user.id)
            has_next = count > 1
            has_prev = False  # На первой странице нет кнопки "назад"
            
            # Показываем объявление с отметкой премиум если нужно
            text = display_announcement_with_keyword(announcement, locale)
            
            try:
                await callback.message.delete()
            except Exception:
                pass
                
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
            )
        else:
            # Если объявление не найдено (маловероятно), просто вернемся к списку
            if announcement_type == "team":
                await process_search_team_menu(callback, locale)
            else:
                await process_search_club_menu(callback, locale)

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
            has_prev = False  # При возврате из меню репорта показываем первое объявление
            text = display_announcement_with_keyword(announcement, locale)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
            )
        else:
            await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def confirm_report(callback: types.CallbackQuery, locale):
    """
    Обработчик подтверждения репорта
    """
    locale = get_user_language(callback.from_user.id)
    data = callback.data.split(":")
    if len(data) >= 5:
        announcement_id = int(data[1])
        reason = data[2]
        announcement_type = data[3]
        confirmed = data[4]
        
        if confirmed == "yes":
            # Записываем репорт в базу данных
            report_announcement(callback.from_user.id, announcement_id, reason)
            await callback.answer(locale["button_report"] + " ✅")
            
            # Здесь можно добавить логику отправки уведомления администратору
            
            # Показываем следующее объявление
            if announcement_type == "team":
                announcement = get_next_announcement("team", callback.from_user.id)
                if announcement:
                    count = get_announcements_count("team", callback.from_user.id)
                    has_next = count > 1
                    has_prev = False  # Для упрощения, после репорта всегда показываем первое объявление
                    premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
                    text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
                    # Отправляем сообщение с фотографией
                    await callback.message.edit_media(
                        types.InputMediaPhoto(
                            media=announcement["image_id"],
                            caption=text
                        ),
                        reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                    )
                else:
                    await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
            elif announcement_type == "club":
                announcement = get_next_announcement("club", callback.from_user.id)
                if announcement:
                    count = get_announcements_count("club", callback.from_user.id)
                    has_next = count > 1
                    has_prev = False  # Для упрощения, после репорта всегда показываем первое объявление
                    premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
                    text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
                    # Отправляем сообщение с фотографией
                    await callback.message.edit_media(
                        types.InputMediaPhoto(
                            media=announcement["image_id"],
                            caption=text
                        ),
                        reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                    )
                else:
                    await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))
        else:
            await callback.answer("Репорт отменен")
    else:
        # Неверный формат данных
        await callback.answer("Ошибка в формате данных")

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
            has_prev = False  # После отмены репорта возвращаем первое объявление
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
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
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

async def process_filtered_search(callback: types.CallbackQuery, locale, announcement_type: str, order: str = "new", state: FSMContext = None):
    """
    Обработчик для поиска объявлений с фильтрацией
    """
    locale = get_user_language(callback.from_user.id)
    announcement_ids = get_filtered_announcement(announcement_type, callback.from_user.id, order)
    
    if not announcement_ids:
        kb = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=kb)
        return
    
    # Берем первое объявление
    announcement_id = announcement_ids[0]
    # Получаем полные данные объявления по ID
    announcement = get_announcement_by_id(announcement_id)
    
    if not announcement:
        kb = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=kb)
        return
        
    text = display_announcement_with_keyword(announcement, locale)
    
    # Проверяем, есть ли еще объявления
    has_next = len(announcement_ids) > 1
    has_prev = False  # На первой странице нет кнопки "назад"
    
    # Сохраняем данные в состоянии (если передан state)
    if state:
        await state.update_data(
            announcement_ids=announcement_ids,
            current_index=0,
            filter_order=order,
            announcement_type=announcement_type
        )
    
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
            has_prev,
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
    # Новый формат: keyword_filter:keyword:type
    parts = callback.data.split(':', 2)
    if len(parts) != 3:
        # Обработка некорректного формата
        await callback.message.edit_text(
            "Ошибка в формате callback_data: " + callback.data,
            reply_markup=search_options_keyboard(locale)
        )
        return
    
    # Получаем keyword и тип объявления из callback_data    
    action, keyword, announcement_type = parts
    
    # Отладочное сообщение для диагностики
    print(f"Filter by keyword: callback_data={callback.data}, extracted parts: action={action}, keyword={keyword}, type={announcement_type}")
    
    # Получаем объявления с выбранным ключевым словом
    # Для "all" используем None, чтобы получить все объявления без фильтрации по ключевому слову
    keyword_filter = None if keyword == "all" else keyword
    
    # Дополнительная отладка - запрос к базе данных
    print(f"Calling get_filtered_announcement with params: type={announcement_type}, keyword={keyword_filter}")
    announcement_ids = get_filtered_announcement(announcement_type, callback.from_user.id, "new", keyword_filter)
    
    # Отладочная информация
    print(f"Found {len(announcement_ids) if announcement_ids else 0} announcements with keyword={keyword_filter}")
    
    # Если объявлений нет, выводим сообщение
    if not announcement_ids:
        # Выводим в консоль дополнительную информацию для диагностики
        print(f"No announcements found for keyword={keyword_filter}, type={announcement_type}")
        
        # Если объявлений нет, возвращаемся в меню поиска
        reply_markup = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=reply_markup)
        return
    
    # Берем первое объявление из списка
    announcement_id = announcement_ids[0]
    
    # Получаем полные данные объявления по ID
    announcement = get_announcement_by_id(announcement_id)
    
    if not announcement:
        print(f"Announcement not found by ID: {announcement_id}")
        # Если объявление не найдено, возвращаемся в меню поиска
        reply_markup = search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=reply_markup)
        return
    
    # Дополнительная отладка - показать найденное объявление
    print(f"Found announcement: id={announcement['id']}, keyword={announcement.get('keyword')}")
    
    # Проверяем, есть ли еще объявления с этим фильтром
    has_next = len(announcement_ids) > 1
    
    # Сохраняем список ID объявлений в состоянии
    await state.update_data(
        announcement_ids=announcement_ids,
        current_index=0,
        filter_keyword=keyword,
        announcement_type=announcement_type
    )
    
    # Отправляем сообщение с фото
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=announcement["image_id"],
        caption=display_announcement_with_keyword(announcement, locale),
        reply_markup=announcement_keyboard(
            locale,
            announcement["id"],
            announcement["user_id"],
            has_next,
            False,  # has_prev всегда False на первой странице
            announcement_type
        )
    )

def display_announcement_with_keyword(announcement, locale):
    # Функция для форматирования отображения объявления с ключевым словом
    keyword_text = ""
    if announcement.get("keyword"):
        keyword_display = locale.get(f"keyword_{announcement['keyword']}", announcement['keyword'])
        keyword_text = "\n" + locale["keyword_label"].format(keyword=keyword_display)
    else:
        # Если ключевое слово не указано, показываем "Нет ключевого слова"
        keyword_text = "\n" + locale["keyword_label"].format(keyword=locale.get("all_keywords", "Все"))
    
    premium_label = "\n" + locale["premium_label"] if announcement.get("is_premium") else ""
    return f"{announcement['description']}{premium_label}{keyword_text}\n\n{locale['time_label']} {announcement['created_at']}"

async def normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("team", callback.from_user.id)
    if announcement:
        count = get_announcements_count("team", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        
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
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "team")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def normal_search_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        
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
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
        )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def my_announcement_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    announcement = get_user_announcement(callback.from_user.id, "team")
    if announcement:
        text = display_announcement_with_keyword(announcement, locale)
        media = types.InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.edit_media(media, reply_markup=announcement_view_keyboard(locale))
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
        text = display_announcement_with_keyword(announcement, locale)
        media = types.InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.edit_media(media, reply_markup=announcement_view_keyboard(locale))
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
    
    # Регистрация для подтверждения просмотра
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_team_confirmation(call, locale, state),
        lambda c: c.data == "process_normal_search_team_confirmation",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_club_confirmation(call, locale, state),
        lambda c: c.data == "process_normal_search_club_confirmation",
        state="*"
    )
    
    # Добавляем обработчики для пагинации - кнопки "Вперед" и "Назад"
    dp.register_callback_query_handler(
        lambda call, state: process_next_team(call, locale, state),
        lambda c: c.data == "next_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_prev_team(call, locale, state),
        lambda c: c.data == "prev_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_next_club(call, locale, state),
        lambda c: c.data == "next_club",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_prev_club(call, locale, state),
        lambda c: c.data == "prev_club",
        state="*"
    )

    # ... остальная регистрация обработчиков
    dp.register_callback_query_handler(
        lambda call, state: process_favorite(call, locale, "team", state),
        lambda c: c.data.startswith("favorite:") and ":team" in c.data,
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_favorite(call, locale, "club", state),
        lambda c: c.data.startswith("favorite:") and ":club" in c.data,
        state="*"
    )
    dp.register_callback_query_handler(lambda call: process_unfavorite(call, locale), lambda c: c.data.startswith("unfavorite:"))
    dp.register_callback_query_handler(lambda call: process_back_report(call, locale), lambda c: c.data.startswith("back_report:"))
    dp.register_callback_query_handler(lambda call: process_report_reason(call, locale), lambda c: c.data.startswith("report_reason:"))
    dp.register_callback_query_handler(lambda call: process_report_selection(call, locale), lambda c: c.data.startswith("confirm_report_selection:"))
    
    dp.register_callback_query_handler(lambda call: delete_announcement(call, locale), lambda c: c.data.startswith("delete_announcement:"))
    dp.register_callback_query_handler(lambda call: get_next_team(call, locale), lambda c: c.data.startswith("next_team"))
    dp.register_callback_query_handler(lambda call: get_next_club(call, locale), lambda c: c.data.startswith("next_club"))
    dp.register_callback_query_handler(
        lambda call, state: filter_new_team(call, locale, state),
        lambda c: c.data == "filter_new_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_old_team(call, locale, state),
        lambda c: c.data == "filter_old_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_premium_team(call, locale, state),
        lambda c: c.data == "filter_premium_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_new_club(call, locale, state),
        lambda c: c.data == "filter_new_club",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_old_club(call, locale, state),
        lambda c: c.data == "filter_old_club",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: filter_premium_club(call, locale, state),
        lambda c: c.data == "filter_premium_club",
        state="*"
    )
    dp.register_callback_query_handler(lambda call: write_to_owner(call, locale), lambda c: c.data.startswith("write:"))
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "team"), lambda c: c.data.startswith("report:") and ":team" in c.data)
    dp.register_callback_query_handler(lambda call: process_report(call, locale, "club"), lambda c: c.data.startswith("report:") and ":club" in c.data)
    dp.register_callback_query_handler(lambda call: process_report_reason(call, locale), lambda c: c.data.startswith("report_reason:"))
    dp.register_callback_query_handler(lambda call: confirm_report(call, locale), lambda c: c.data.startswith("confirm_report:"))
    dp.register_callback_query_handler(lambda call: cancel_report(call, locale), lambda c: c.data.startswith("cancel_report:"))
    dp.register_callback_query_handler(
        lambda call, state: confirm_normal_search_team(call, locale, state),
        lambda c: c.data == "confirm_normal_search_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: confirm_normal_search_club(call, locale, state),
        lambda c: c.data == "confirm_normal_search_club",
        state="*"
    )

    # Регистрация обработчиков для фильтров по ключевым словам
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
        lambda c: c.data.startswith("keyword_filter:"),
        state="*"
    )

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

async def filter_new_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "new", state)

async def filter_old_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "old", state)

async def filter_premium_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "team", "premium", state)

async def filter_new_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "new", state)

async def filter_old_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "old", state)

async def filter_premium_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_filtered_search(callback, locale, "club", "premium", state)

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

async def confirm_normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Подтверждение перехода к обычному поиску команды
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_team(callback, locale, state)
    
async def confirm_normal_search_club(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Подтверждение перехода к обычному поиску клуба
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await process_normal_search_club(callback, locale, state)

