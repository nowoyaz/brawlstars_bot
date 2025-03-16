from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database.session import SessionLocal
from database.models import Announcement, User
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
    get_paginated_announcements,
    get_user_language,
    record_section_visit
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
import logging

logger = logging.getLogger(__name__)

def display_announcement_with_keyword(announcement, locale):
    """
    Функция для форматирования отображения объявления с ключевым словом
    """
    if not announcement:
        return None
    
    # Добавляем метку Premium, если пользователь премиум
    premium_label = locale["premium_label"] + "\n" if announcement.get("is_premium") else ""
    
    # Добавляем метку ключевого слова
    keyword_label = ""
    if announcement.get("keyword"):
        keyword_text = locale.get(f"keyword_{announcement['keyword']}", announcement['keyword'])
        keyword_label = locale["keyword_label"].format(keyword=keyword_text) + "\n"
    
    # Добавляем время создания
    time_label = locale["time_label"] + " " + announcement["created_at"] + "\n"
    
    # Формируем полный текст
    return f"{premium_label}{keyword_label}{time_label}{announcement['description']}"

# ----- Меню поиска -----

async def process_search_team_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "search_team_menu")
    
    text = locale["search_team_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_team_menu_keyboard(locale))

async def process_search_club_menu(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "search_club_menu")
    
    text = locale["search_club_menu_text"]
    await callback.message.edit_text(text, reply_markup=search_club_menu_keyboard(locale))

# ----- "Мое объявление" -----

async def process_my_announcement(callback: types.CallbackQuery, locale, announcement_type: str):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем данные о статусе премиума и объявлениях пользователя
    is_premium = is_user_premium(callback.from_user.id)
    
    # Если пользователь не премиум, проверяем наличие объявления в другой категории
    if not is_premium:
        opposite_type = "club" if announcement_type == "team" else "team"
        opposite = get_user_announcement(callback.from_user.id, opposite_type)
        if opposite:
            await callback.message.edit_text(
                locale["no_premium_announcement_limit_reached"],
                reply_markup=inline_main_menu_keyboard(locale)
            )
            return
    
    # Получаем объявления пользователя данного типа
    announcements = get_user_announcement(callback.from_user.id, announcement_type, get_all=True)
    
    if announcements:
        # Если объявлений несколько (у премиум-пользователя), показываем список
        if is_premium and len(announcements) > 1:
            # Создаем клавиатуру для выбора объявления
            kb = types.InlineKeyboardMarkup(row_width=1)
            
            for i, announcement in enumerate(announcements, 1):
                created_at = announcement["created_at"]
                kb.add(types.InlineKeyboardButton(
                    text=f"Объявление {i} от {created_at}", 
                    callback_data=f"view_my_announcement:{announcement['id']}"
                ))
            
            if len(announcements) < 2:  # Если объявлений меньше максимума
                kb.add(types.InlineKeyboardButton(
                    text=locale["button_create_new"], 
                    callback_data=f"create_new_{announcement_type}"
                ))
                
            kb.add(types.InlineKeyboardButton(
                text=locale["button_back"], 
                callback_data="back_to_search_menu"
            ))
            
            await callback.message.edit_text(
                locale["my_announcements_list"].format(count=len(announcements), type=announcement_type),
                reply_markup=kb
            )
        else:
            # Если объявление одно, сразу показываем его
            announcement = announcements[0]
            text = display_announcement_with_keyword(announcement, locale)
            try:
                media_type = announcement.get("media_type", "photo")
                
                if media_type == "photo":
                    media = types.InputMediaPhoto(announcement["image_id"], caption=text)
                elif media_type == "video":
                    media = types.InputMediaVideo(announcement["image_id"], caption=text)
                elif media_type == "animation":
                    media = types.InputMediaAnimation(announcement["image_id"], caption=text)
                else:
                    media = types.InputMediaPhoto(announcement["image_id"], caption=text)
                    
                await callback.message.edit_media(media, reply_markup=announcement_view_keyboard(locale))
            except Exception as e:
                logger.error(f"Error showing announcement: {str(e)}")
                await callback.message.edit_text(
                    f"Ошибка при отображении объявления: {str(e)}",
                    reply_markup=inline_main_menu_keyboard(locale)
                )
    else:
        # Если объявлений нет, предлагаем создать новое
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

async def process_normal_search_team(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Обработчик для перехода к просмотру обычных объявлений поиска команды
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Сбрасываем индекс просмотра на 0 при первом просмотре
    await state.update_data(announcement_page=0)
    
    # Сразу показываем первое объявление
    announcement = get_next_announcement("team", callback.from_user.id)
    if announcement:
        count = get_announcements_count("team", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_team_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "team")
            )
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "team")
            )
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "team")
            )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_club(callback: types.CallbackQuery, locale, state: FSMContext):
    """
    Обработчик для перехода к просмотру обычных объявлений поиска клуба
    """
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Сбрасываем индекс просмотра на 0 при первом просмотре
    await state.update_data(announcement_page=0)
    
    # Сразу показываем первое объявление
    announcement = get_next_announcement("club", callback.from_user.id)
    if announcement:
        count = get_announcements_count("club", callback.from_user.id)
        has_next = count > 1
        has_prev = False  # На первой странице нет кнопки "назад"
        
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_club_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
            await callback.message.bot.send_photo(
                callback.from_user.id,
                photo=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
            )
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
            )
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
                caption=text,
                reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, "club")
            )
    else:
        await callback.message.edit_text(locale["no_announcements"], reply_markup=inline_main_menu_keyboard(locale))

async def process_normal_search_team_confirmation(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    text = locale["normal_search_advice_text"]
    await callback.message.edit_text(text, reply_markup=confirmation_keyboard(locale, suffix="team"))

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
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_team_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
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
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
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
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
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
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_team_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
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
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
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
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
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
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_club_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
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
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
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
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
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
        # Сохраняем ID объявления в состоянии
        await state.update_data(current_club_announcement_id=announcement["id"])
        
        # Используем функцию для отображения с ключевым словом
        text = display_announcement_with_keyword(announcement, locale)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Определяем тип медиа и отправляем соответствующим методом
        media_type = announcement.get("media_type", "photo")
        if media_type == "photo":
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
        elif media_type == "video":
            await callback.message.bot.send_video(
                callback.from_user.id,
                video=announcement["image_id"],
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
        else:  # animation (GIF)
            await callback.message.bot.send_animation(
                callback.from_user.id,
                animation=announcement["image_id"],
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
                
            # Определяем тип медиа и отправляем соответствующим методом
            media_type = announcement.get("media_type", "photo")
            if media_type == "photo":
                await callback.message.bot.send_photo(
                    callback.from_user.id,
                    photo=announcement["image_id"],
                    caption=text,
                    reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                )
            elif media_type == "video":
                await callback.message.bot.send_video(
                    callback.from_user.id,
                    video=announcement["image_id"],
                    caption=text,
                    reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                )
            else:  # animation (GIF)
                await callback.message.bot.send_animation(
                    callback.from_user.id,
                    animation=announcement["image_id"],
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
                # Определяем тип медиа и отправляем соответствующим методом
                media_type = announcement.get("media_type", "photo")
                if media_type == "photo":
                    await callback.bot.send_photo(
                        ADMIN_ID,
                        photo=announcement["image_id"],
                        caption=text,
                        reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
                    )
                elif media_type == "video":
                    await callback.bot.send_video(
                        ADMIN_ID,
                        video=announcement["image_id"],
                        caption=text,
                        reply_markup=report_admin_keyboard(locale, announcement["user_id"], callback.from_user.id)
                    )
                else:  # animation (GIF)
                    await callback.bot.send_animation(
                        ADMIN_ID,
                        animation=announcement["image_id"],
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
        else:  # club
            next_ann = get_next_announcement("club", callback.from_user.id)
            if next_ann:
                await process_normal_search_club(callback, locale)
            else:
                await callback.message.bot.send_message(
                    callback.from_user.id, 
                    locale["no_announcements"], 
                    reply_markup=inline_main_menu_keyboard(locale)
                )

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
                    reply_markup=report_confirmation_keyboard(locale, announcement_id, announcement_type, reason)
                )
            else:
                await callback.message.edit_text(
                    confirm_text,
                    reply_markup=report_confirmation_keyboard(locale, announcement_id, announcement_type, reason)
                )
        except Exception:
            # На случай ошибок отправляем новое сообщение
            await callback.message.bot.send_message(
                callback.from_user.id,
                confirm_text,
                reply_markup=report_confirmation_keyboard(locale, announcement_id, announcement_type, reason)
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
                
            # Определяем тип медиа и отправляем соответствующим методом
            media_type = announcement.get("media_type", "photo")
            if media_type == "photo":
                await callback.message.bot.send_photo(
                    callback.from_user.id,
                    photo=announcement["image_id"],
                    caption=text,
                    reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                )
            elif media_type == "video":
                await callback.message.bot.send_video(
                    callback.from_user.id,
                    video=announcement["image_id"],
                    caption=text,
                    reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                )
            else:  # animation (GIF)
                await callback.message.bot.send_animation(
                    callback.from_user.id,
                    animation=announcement["image_id"],
                    caption=text,
                    reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                )

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
                    text = display_announcement_with_keyword(announcement, locale)
                    
                    # Определяем тип медиа и отправляем соответствующим методом
                    media_type = announcement.get("media_type", "photo")
                    if media_type == "photo":
                        await callback.message.edit_media(
                            types.InputMediaPhoto(
                                media=announcement["image_id"],
                                caption=text
                            ),
                            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                        )
                    elif media_type == "video":
                        await callback.message.edit_media(
                            types.InputMediaVideo(
                                media=announcement["image_id"],
                                caption=text
                            ),
                            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                        )
                    else:  # animation (GIF)
                        await callback.message.edit_media(
                            types.InputMediaAnimation(
                                media=announcement["image_id"],
                                caption=text
                            ),
                            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, has_prev, announcement_type)
                        )

# ----- Фильтрация -----

async def process_filtered_search(callback: types.CallbackQuery, locale):
    """Обработчик для фильтрованного поиска по времени/премиум-статусу"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем тип фильтра из callback_data
    filter_parts = callback.data.split("_")
    if len(filter_parts) < 4:
        await callback.message.edit_text("Ошибка в выборе фильтра", reply_markup=search_options_keyboard(locale))
        return
    
    announcement_type = filter_parts[2]  # team или club
    filter_type = filter_parts[3]  # new, old или premium
    
    # Логика фильтрации объявлений
    session = SessionLocal()
    query = session.query(Announcement).filter(Announcement.announcement_type == announcement_type)
    
    # Применяем фильтр
    if filter_type == "new":
        query = query.order_by(Announcement.created_at.desc())
    elif filter_type == "old":
        query = query.order_by(Announcement.created_at)
    elif filter_type == "premium":
        # Получаем ID пользователей с премиум-статусом
        premium_users = session.query(User.id).filter(User.is_premium == True).all()
        premium_user_ids = [user.id for user in premium_users]
        
        # Фильтруем объявления по премиум-пользователям
        if premium_user_ids:
            query = query.filter(Announcement.user_id.in_(premium_user_ids))
            query = query.order_by(Announcement.created_at.desc())
        else:
            # Если нет премиум-пользователей, показываем сообщение
            session.close()
            await callback.message.edit_text(
                locale.get("no_premium_announcements", "🔍 Премиум-объявления не найдены"),
                reply_markup=search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
            )
            return
    
    # Получаем первое объявление
    announcement = query.first()
    session.close()
    
    if not announcement:
        # Если объявления не найдены, показываем сообщение
        await callback.message.edit_text(
            locale.get("no_announcements", "📝 Объявления не найдены"),
            reply_markup=search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        )
        return
    
    # Показываем найденное объявление
    await show_announcement(callback, announcement, locale, announcement_type)

async def show_filters_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущее объявление (если оно есть)
    data = await state.get_data()
    user_announcement = data.get('user_announcement', None)
    
    if user_announcement:
        # Если у пользователя уже есть объявление, проверяем его статус
        session = SessionLocal()
        announcement = session.query(Announcement).filter(
            Announcement.id == user_announcement,
            Announcement.user_id == callback.from_user.id
        ).first()
        session.close()
        
        if announcement:
            # Если объявление найдено, предлагаем редактировать его
            # Логика для редактирования объявления...
            return
    
    # Показываем фильтры по времени и премиум-статусу
    buttons = [
        types.InlineKeyboardButton(text=locale["filter_new"], callback_data=f"filtered_search_team_new"),
        types.InlineKeyboardButton(text=locale["filter_old"], callback_data=f"filtered_search_team_old"),
        types.InlineKeyboardButton(text=locale["filter_premium"], callback_data=f"filtered_search_team_premium")
    ]
    
    # Добавляем кнопку для фильтрации по ключевым словам
    buttons.append(types.InlineKeyboardButton(text=locale.get("filter_by_keyword", "🏷 По ключевым словам"), callback_data="show_keyword_filters_team"))
    
    # Кнопка "Назад"
    buttons.append(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    for button in buttons:
        kb.add(button)
    
    await callback.message.edit_text(locale["search_filters"], reply_markup=kb)

async def show_keyword_filters_team(callback: types.CallbackQuery, locale):
    """Показывает фильтры по ключевым словам для команд"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    kb = keyword_filter_keyboard(locale, "team")
    
    await callback.message.edit_text(
        locale.get("filter_by_keyword", "🏷 Выберите ключевое слово:"),
        reply_markup=kb
    )

async def process_keyword_filter(callback: types.CallbackQuery, locale):
    """Обработчик для фильтрации по ключевым словам"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем параметры из callback_data
    filter_parts = callback.data.split(":")
    if len(filter_parts) < 3:
        await callback.message.edit_text("Ошибка в выборе фильтра", reply_markup=search_options_keyboard(locale))
        return
    
    keyword = filter_parts[1]  # all, trophy_modes, ranked, club_events, map_maker или other
    announcement_type = filter_parts[2]  # team или club
    
    # Если выбрано "all", показываем все объявления
    if keyword == "all":
        await normal_search_team(callback, locale) if announcement_type == "team" else normal_search_club(callback, locale)
        return
    
    # Логика фильтрации объявлений по ключевому слову
    session = SessionLocal()
    query = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.keyword == keyword
    ).order_by(Announcement.created_at.desc())
    
    # Получаем первое объявление
    announcement = query.first()
    session.close()
    
    if not announcement:
        # Если объявления не найдены, показываем сообщение
        await callback.message.edit_text(
            locale.get("no_announcements_with_keyword", "📝 Объявления с выбранным ключевым словом не найдены"),
            reply_markup=search_options_keyboard(locale) if announcement_type == "team" else search_options_club_keyboard(locale)
        )
        return
    
    # Показываем найденное объявление
    await show_announcement(callback, announcement, locale, announcement_type)

async def show_filters_club(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    text = locale["filter_options_text"]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text="🆕 " + locale["filter_new"], callback_data="filtered_search_club_new"),
        types.InlineKeyboardButton(text="🔄 " + locale["filter_old"], callback_data="filtered_search_club_old"),
        types.InlineKeyboardButton(text="⭐ " + locale["filter_premium"], callback_data="filtered_search_club_premium")
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
    
    # Извлекаем данные из callback
    data = callback.data.split(":")
    if len(data) < 3:
        print("Invalid callback data format")
        return
    
    keyword = data[1]
    announcement_type = data[2]
    
    # Для "all" используем None, чтобы получить все объявления без фильтрации
    keyword_filter = None if keyword == "all" else keyword
    
    # Получаем отфильтрованные объявления
    announcement_ids = get_filtered_announcement(announcement_type, callback.from_user.id, "new", keyword_filter)
    if not announcement_ids:
        print(f"No announcements found for filter: type={announcement_type}, keyword={keyword_filter}")
        # Если объявлений нет, возвращаемся в меню поиска
        if announcement_type == "team":
            reply_markup = search_options_keyboard(locale)
        else:
            reply_markup = search_options_club_keyboard(locale)
        await callback.message.edit_text(locale["no_announcements"], reply_markup=reply_markup)
        return
    
    # Получаем первое объявление
    announcement_id = announcement_ids[0]
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
        filter_keyword=keyword_filter,
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

async def display_announcement(message: types.Message, announcement: dict, locale, keyboard=None):
    """Отображает объявление с учетом типа медиа"""
    if not announcement:
        await message.answer(locale["no_announcements"])
        return

    # Добавляем метку Premium, если пользователь премиум
    premium_label = locale["premium_label"] + "\n" if announcement.get("is_premium") else ""
    
    # Добавляем метку ключевого слова
    keyword_label = ""
    if announcement.get("keyword"):
        keyword_text = locale.get(f"keyword_{announcement['keyword']}", announcement['keyword'])
        keyword_label = locale["keyword_label"].format(keyword=keyword_text) + "\n"
    
    # Добавляем время создания
    time_label = locale["time_label"] + " " + announcement["created_at"] + "\n"
    
    # Формируем полный текст
    caption = f"{premium_label}{keyword_label}{time_label}{announcement['description']}"

    # Отправляем медиа в зависимости от его типа
    media_type = announcement.get("media_type", "photo")
    if media_type == "photo":
        await message.answer_photo(
            photo=announcement["image_id"],
            caption=caption,
            reply_markup=keyboard
        )
    elif media_type == "video":
        await message.answer_video(
            video=announcement["image_id"],
            caption=caption,
            reply_markup=keyboard
        )
    else:  # animation (GIF)
        await message.answer_animation(
            animation=announcement["image_id"],
            caption=caption,
            reply_markup=keyboard
        )

async def show_announcement(callback, announcement, locale, announcement_type):
    """Показывает объявление пользователю"""
    
    # Получаем данные пользователя, создавшего объявление
    session = SessionLocal()
    user = session.query(User).filter(User.id == announcement.user_id).first()
    session.close()
    
    # Формируем текст объявления
    text = f"📝 {announcement.description}\n\n"
    
    # Добавляем метку премиум-пользователя, если применимо
    if user and user.is_premium:
        text += f"{locale.get('premium_label', '🪙 PREMIUM')}\n"
    
    # Добавляем время публикации
    created_time = announcement.created_at.strftime("%d.%m.%Y %H:%M")
    text += f"{locale.get('time_label', '🕒')} {created_time}\n"
    
    # Добавляем ключевое слово, если оно есть
    if announcement.keyword and announcement.keyword != "skip":
        keyword_text = locale.get(f"keyword_{announcement.keyword}", announcement.keyword.capitalize())
        text += f"{locale.get('keyword_label', '🏷 Ключевое слово')}: {keyword_text}\n"
    
    # Проверяем, есть ли другие объявления этого типа
    session = SessionLocal()
    announcements_count = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type
    ).count()
    session.close()
    
    has_next = announcements_count > 1
    has_prev = False  # Для первого объявления нет предыдущих
    
    # Отправляем сообщение с объявлением
    await callback.message.delete()
    
    # Определяем тип медиа и отправляем соответствующим методом
    media_type = announcement.media_type if hasattr(announcement, 'media_type') else "photo"
    
    if media_type == "photo":
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=announcement.image_id,
            caption=text,
            reply_markup=announcement_keyboard(
                locale,
                announcement.id,
                announcement.user_id,
                has_next,
                has_prev,
                announcement_type
            )
        )
    elif media_type == "video":
        await callback.message.bot.send_video(
            chat_id=callback.from_user.id,
            video=announcement.image_id,
            caption=text,
            reply_markup=announcement_keyboard(
                locale,
                announcement.id,
                announcement.user_id,
                has_next,
                has_prev,
                announcement_type
            )
        )
    else:  # animation (GIF)
        await callback.message.bot.send_animation(
            chat_id=callback.from_user.id,
            animation=announcement.image_id,
            caption=text,
            reply_markup=announcement_keyboard(
                locale,
                announcement.id,
                announcement.user_id,
                has_next,
                has_prev,
                announcement_type
            )
        )

async def my_announcement_team(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Проверяем, есть ли у пользователя премиум
    has_premium = is_user_premium(callback.from_user.id)
    
    # Получаем все объявления пользователя (до 2-х для премиум)
    announcements = get_user_announcement(callback.from_user.id, "team", get_all=True)
    
    if announcements:
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Создаем список для хранения сообщений об объявлениях
        kb = types.InlineKeyboardMarkup(row_width=1)
        
        # Для каждого объявления создаем кнопку просмотра
        for ann in announcements:
            kb.add(types.InlineKeyboardButton(
                text=f"{locale.get('announcement_view_button', 'Просмотреть объявление')} #{ann['id']}",
                callback_data=f"view_my_announcement:{ann['id']}"
            ))
        
        # Добавляем кнопку создания нового объявления, если у пользователя премиум и менее 2-х объявлений
        if has_premium and len(announcements) < 2:
            kb.add(types.InlineKeyboardButton(text=locale["button_create"], callback_data="create_new_team"))
        
        # Добавляем кнопку назад
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        
        # Отправляем список объявлений
        await callback.message.bot.send_message(
            chat_id=callback.from_user.id,
            text=locale.get("my_announcements_list", "Ваши объявления о поиске команды:"),
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
    
    # Проверяем, есть ли у пользователя премиум
    has_premium = is_user_premium(callback.from_user.id)
    
    # Получаем все объявления пользователя (до 2-х для премиум)
    announcements = get_user_announcement(callback.from_user.id, "club", get_all=True)
    
    if announcements:
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Создаем список для хранения сообщений об объявлениях
        kb = types.InlineKeyboardMarkup(row_width=1)
        
        # Для каждого объявления создаем кнопку просмотра
        for ann in announcements:
            kb.add(types.InlineKeyboardButton(
                text=f"{locale.get('announcement_view_button', 'Просмотреть объявление')} #{ann['id']}",
                callback_data=f"view_my_announcement:{ann['id']}"
            ))
        
        # Добавляем кнопку создания нового объявления, если у пользователя премиум и менее 2-х объявлений
        if has_premium and len(announcements) < 2:
            kb.add(types.InlineKeyboardButton(text=locale["button_create"], callback_data="create_new_club"))
        
        # Добавляем кнопку назад
        kb.add(types.InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
        
        # Отправляем список объявлений
        await callback.message.bot.send_message(
            chat_id=callback.from_user.id,
            text=locale.get("my_announcements_list_club", "Ваши объявления о поиске клуба:"),
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

# ----- Админские функции -----

async def admin_block_user(callback: types.CallbackQuery):
    """
    Обработчик для блокировки пользователя администратором.
    Вызывается когда администратор нажимает на кнопку блокировки после получения репорта.
    """
    await callback.answer("Пользователь заблокирован ✅")
    
    # Получаем ID пользователя из callback.data
    data = callback.data.split(":")
    if len(data) >= 2:
        user_id = int(data[1])
        
        # Блокируем пользователя в базе данных
        session = SessionLocal()
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_banned = True
            session.commit()
            
            # Отправляем уведомление пользователю о блокировке
            try:
                await callback.bot.send_message(
                    user.tg_id,
                    "⛔ Ваш аккаунт был заблокирован администратором за нарушение правил."
                )
            except Exception:
                pass
        session.close()
        
        # Отвечаем администратору
        await callback.message.edit_caption(
            caption=f"Пользователь с ID {user_id} заблокирован."
        )

async def admin_block_reporter(callback: types.CallbackQuery):
    """
    Обработчик для блокировки пользователя, отправившего репорт.
    Используется в случаях, когда репорт оказался ложным.
    """
    await callback.answer("Отправитель репорта заблокирован ✅")
    
    # Получаем ID отправителя репорта из callback.data
    data = callback.data.split(":")
    if len(data) >= 2:
        reporter_id = int(data[1])
        
        # Блокируем пользователя в базе данных
        session = SessionLocal()
        user = session.query(User).filter(User.id == reporter_id).first()
        if user:
            user.is_banned = True
            session.commit()
            
            # Отправляем уведомление пользователю о блокировке
            try:
                await callback.bot.send_message(
                    user.tg_id,
                    "⛔ Ваш аккаунт был заблокирован администратором за ложные жалобы."
                )
            except Exception:
                pass
        session.close()
        
        # Отвечаем администратору
        await callback.message.edit_caption(
            caption=f"Отправитель репорта с ID {reporter_id} заблокирован."
        )

async def admin_ignore_report(callback: types.CallbackQuery):
    """
    Обработчик для игнорирования репорта администратором.
    """
    await callback.answer("Репорт проигнорирован ✅")
    
    # Отвечаем администратору
    await callback.message.edit_caption(
        caption="Репорт проигнорирован. Никаких действий не предпринято."
    )

# Класс для фильтра проверки администратора
class IsAdmin(object):
    """
    Фильтр для проверки, является ли пользователь администратором
    """
    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def __call__(self, obj):
        if self.is_admin:
            # Проверяем, является ли пользователь администратором
            user_id = obj.from_user.id
            return user_id == ADMIN_ID
        return True

# ----- Регистрация обработчиков -----

def register_handlers_search(dp: Dispatcher, locale):
    # Начальные меню поиска
    dp.register_callback_query_handler(
        lambda call: process_search_team_menu(call, locale),
        lambda c: c.data == "search_team_menu"
    )
    dp.register_callback_query_handler(
        lambda call: process_search_club_menu(call, locale),
        lambda c: c.data == "search_club_menu"
    )
    
    # Обработчики для кнопки "Поиск" в меню поиска команды/клуба
    dp.register_callback_query_handler(
        lambda call: process_search_team_options(call, locale),
        lambda c: c.data == "search_team_search"
    )
    dp.register_callback_query_handler(
        lambda call: process_search_club_options(call, locale),
        lambda c: c.data == "search_club_search"
    )
    
    # Обработчики для поиска (обычный/с фильтрами)
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_team(call, locale, state),
        lambda c: c.data == "normal_search_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_club(call, locale, state),
        lambda c: c.data == "normal_search_club",
        state="*"
    )
    
    # Обработчики для фильтров
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
    
    # Обработчик для показа фильтров по ключевым словам
    dp.register_callback_query_handler(
        lambda call: show_keyword_filters_team(call, locale),
        lambda c: c.data == "show_keyword_filters_team",
        state="*"
    )
    
    # Обработчики для фильтрованного поиска
    dp.register_callback_query_handler(
        lambda call: process_filtered_search(call, locale),
        lambda c: c.data.startswith("filtered_search_"),
        state="*"
    )
    
    # Обработчики для фильтрации по ключевым словам
    dp.register_callback_query_handler(
        lambda call: process_keyword_filter(call, locale),
        lambda c: c.data.startswith("keyword_filter:"),
        state="*"
    )
    
    # Обработчики для обработки подтверждений
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_team_confirmation(call, locale, state),
        lambda c: c.data == "confirm_normal_search_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_normal_search_club_confirmation(call, locale, state),
        lambda c: c.data == "confirm_normal_search_club",
        state="*"
    )
    
    # Обработчики для репортов
    dp.register_callback_query_handler(
        lambda call: process_report(call, locale, "team"),
        lambda c: c.data.startswith("report:")
    )
    dp.register_callback_query_handler(
        lambda call: process_report_selection(call, locale),
        lambda c: c.data.startswith("confirm_report_selection:")
    )
    dp.register_callback_query_handler(
        lambda call: confirm_report(call, locale),
        lambda c: c.data.startswith("confirm_report:")
    )
    dp.register_callback_query_handler(
        lambda call: process_back_report(call, locale),
        lambda c: c.data.startswith("cancel_report:")
    )
    dp.register_callback_query_handler(
        lambda call: process_back_report(call, locale),
        lambda c: c.data.startswith("back_report:")
    )
    
    # Обработчики для админских команд
    dp.register_callback_query_handler(
        admin_block_user,
        lambda c: c.data.startswith("admin_block:"),
        IsAdmin(True)
    )
    dp.register_callback_query_handler(
        admin_block_reporter,
        lambda c: c.data.startswith("admin_block_reporter:"),
        IsAdmin(True)
    )
    dp.register_callback_query_handler(
        admin_ignore_report,
        lambda c: c.data == "admin_ignore",
        IsAdmin(True)
    )
    
    # Фильтры и объявления пользователя
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

    # Обработчики для возврата в меню поиска
    dp.register_callback_query_handler(
        lambda call, state: process_back_to_search_menu(call, locale),
        lambda c: c.data == "back_to_search_menu",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_back_to_search_options_menu(call, locale),
        lambda c: c.data == "back_to_search_options_menu",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: process_back_to_search_options_menu(call, locale),
        lambda c: c.data == "back_to_search_options_club_menu",
        state="*"
    )

    dp.register_callback_query_handler(
        lambda call, state: filter_by_keyword(call, locale, state),
        lambda c: c.data == "skip_keyword",
        state="*"
    )
    
    # Обработчики для избранного
    dp.register_callback_query_handler(
        lambda call: process_favorite(call, locale, "team", None),
        lambda c: c.data.startswith("favorite:")
    )
    dp.register_callback_query_handler(
        lambda call: process_unfavorite(call, locale),
        lambda c: c.data.startswith("unfavorite:")
    )
    
    # Обработчики для перехода между объявлениями
    dp.register_callback_query_handler(
        lambda call, state: process_next_team(call, locale, state),
        lambda c: c.data.startswith("next_")
    )
    dp.register_callback_query_handler(
        lambda call, state: process_prev_team(call, locale, state),
        lambda c: c.data.startswith("prev_")
    )