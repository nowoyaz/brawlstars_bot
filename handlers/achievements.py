import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User, Achievement, UserAchievement
from utils.achievements import format_achievements_message, check_and_award_achievements, ACHIEVEMENTS
from keyboards.inline_keyboard import (
    achievements_keyboard, 
    back_to_achievements_keyboard, 
    buy_achievement_confirm_keyboard,
    profile_view_keyboard,
    search_team_menu_keyboard,
    search_club_menu_keyboard,
    announcement_keyboard
)
from database.achievements import (
    get_user_achievements, 
    get_available_achievements, 
    buy_achievement, 
    record_secret_purchase,
    has_purchased_secret,
    initialize_achievements,
    check_coins_achievement,
    ACHIEVEMENT_MAJOR
)
from utils.helpers import (
    get_user_language,
    get_announcement_by_id,
    get_favorites_list,
    get_announcements_count
)
from aiogram.utils.exceptions import MessageNotModified
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.search import display_announcement_with_keyword
from handlers.favorites import send_new_announcement_media
from aiogram.dispatcher import FSMContext

logger = logging.getLogger(__name__)

SECRET_VIDEO_PRICE = 5000
SECRET_VIDEO_KEY = "bubbs_video"

# Текст для секретного видео
SECRET_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Заменить на реальную ссылку
SECRET_VIDEO_TEXT = "🔥 Секретный ролик бубса! Наслаждайтесь просмотром: "


async def show_achievements(callback: types.CallbackQuery, locale):
    """Показывает список достижений пользователя"""
    try:
        logging.info(f"Raw callback data received: '{callback.data}'")
        logging.info(f"Callback type: {type(callback.data)}")
        logging.info(f"User ID: {callback.from_user.id}")
        
        # Отвечаем на callback
        try:
            await callback.answer("Загрузка достижений...")
        except Exception as e:
            logging.error(f"Error answering callback: {e}")
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_id == callback.from_user.id).first()
            if not user:
                logging.info(f"Creating new user with ID {callback.from_user.id}")
                user = User(id=callback.from_user.id, tg_id=callback.from_user.id)
                db.add(user)
                db.commit()
            
            achievements = user.achievements or []
            message = format_achievements_message(achievements, locale)
            
            try:
                await callback.message.edit_text(
                    text=message,
                    reply_markup=achievements_keyboard(locale)
                )
                logging.info("Message edited successfully")
            except Exception as e:
                logging.error(f"Error editing message: {e}")
                await callback.message.answer(
                    text=message,
                    reply_markup=achievements_keyboard(locale)
                )
                logging.info("Sent new message as fallback")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Global error in show_achievements: {e}")


async def cmd_achievements(callback: types.CallbackQuery, locale):
    """Обработчик для раздела достижений"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем количество достижений пользователя
    user_achievements = get_user_achievements(callback.from_user.id)
    total_achievements = len(ACHIEVEMENTS)
    count = len(user_achievements) if user_achievements else 0
    
    text = locale.get("achievements_text", "🏆 Ваши достижения: {count}/{total}").format(
        count=count, 
        total=total_achievements
    )
    kb = achievements_keyboard(locale)
    
    await safe_edit_message(callback.message, text, reply_markup=kb)


async def process_my_achievements(callback: types.CallbackQuery, locale):
    """Обработчик для просмотра достижений пользователя"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Проверяем достижение "Липрикон" (если у пользователя есть 15000+ монет)
    check_coins_achievement(callback.from_user.id)
    
    # Получаем достижения пользователя
    user_achievements = get_user_achievements(callback.from_user.id)
    
    if not user_achievements:
        text = locale.get("no_achievements", "🏅 У вас пока нет достижений. Попробуйте выполнить некоторые действия, чтобы их получить!")
    else:
        text = locale.get("achievements_list", "📋 Список ваших достижений:") + "\n\n"
        
        for achievement in user_achievements:
            achieved_date = achievement['achieved_at'].strftime("%d.%m.%Y")
            text += f"{achievement['icon']} {achievement['name']} - {achievement['description']}\n"
            text += locale.get("achievement_date", "📅 Получено: {date}").format(date=achieved_date) + "\n\n"
    
    kb = back_to_achievements_keyboard(locale)
    
    await safe_edit_message(callback.message, text, reply_markup=kb)


async def process_available_achievements(callback: types.CallbackQuery, locale):
    """Обработчик для просмотра доступных достижений"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем доступные достижения
    available_achievements = get_available_achievements(callback.from_user.id)
    
    if not available_achievements:
        text = locale.get("no_available_achievements", "🎖 Поздравляем! Вы получили все доступные достижения!")
    else:
        text = locale.get("achievements_available", "📋 Доступные достижения:") + "\n\n"
        
        for achievement in available_achievements:
            text += f"{achievement.icon} {achievement.name} - {achievement.description}\n"
            
            if achievement.is_purchasable:
                text += locale.get("achievement_price", "🎁 Цена: {price} монет").format(price=achievement.price) + "\n"
            
            text += "\n"
    
    kb = back_to_achievements_keyboard(locale)
    
    await safe_edit_message(callback.message, text, reply_markup=kb)


async def process_buy_achievement(callback: types.CallbackQuery, locale):
    """Обработчик для покупки достижений"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем доступные покупаемые достижения
    available_achievements = get_available_achievements(callback.from_user.id)
    purchasable_achievements = [a for a in available_achievements if a.is_purchasable]
    
    if not purchasable_achievements:
        text = locale.get("no_purchasable_achievements", "🛒 У вас нет доступных для покупки достижений.")
    else:
        text = locale.get("buy_achievement_text", "💰 Выберите достижение для покупки:") + "\n\n"
        
        for achievement in purchasable_achievements:
            text += f"{achievement.icon} {achievement.name} - {achievement.description}\n"
            text += locale.get("achievement_price", "🎁 Цена: {price} монет").format(price=achievement.price) + "\n\n"
    
    # Создаем клавиатуру
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    # Если есть достижение "Мажор", добавляем кнопку для его покупки
    major_achievement = next((a for a in purchasable_achievements if a.key == ACHIEVEMENT_MAJOR), None)
    if major_achievement:
        kb.add(types.InlineKeyboardButton(
            text=locale.get("button_buy", "💰 Купить"), 
            callback_data=f"confirm_buy_achievement:{major_achievement.id}"
        ))
    
    # Добавляем кнопку отмены
    kb.add(types.InlineKeyboardButton(
        text=locale.get("button_cancel", "🔙 Отмена"), 
        callback_data="back_to_achievements"
    ))
    
    await safe_edit_message(callback.message, text, reply_markup=kb)


async def process_confirm_buy_achievement(callback: types.CallbackQuery, locale):
    """Обработчик для подтверждения покупки достижения"""
    locale = get_user_language(callback.from_user.id)
    
    # Получаем ID достижения из callback_data
    achievement_id = int(callback.data.split(":")[1])
    
    # Получаем ключ достижения по ID (предполагается, что это "Мажор")
    achievement_key = ACHIEVEMENT_MAJOR
    
    # Получаем информацию о достижении
    db = SessionLocal()
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    db.close()
    
    # Покупаем достижение
    result = buy_achievement(callback.from_user.id, achievement_key)
    
    if result["success"]:
        text = locale.get("buy_achievement_success", "✅ Вы успешно приобрели достижение: {name}").format(name=achievement.name)
    else:
        if result["reason"] == "not_enough_coins":
            # Получаем текущий баланс пользователя
            db = SessionLocal()
            user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
            user_crystals = user.crystals if user else 0
            db.close()
            
            text = locale.get("buy_achievement_not_enough_coins", "❌ Недостаточно монет. У вас {balance}, но нужно {price}").format(
                balance=user_crystals,
                price=achievement.price
            )
        elif result["reason"] == "already_awarded":
            text = locale.get("buy_achievement_already_owned", "❌ У вас уже есть это достижение")
        else:
            text = locale.get("buy_achievement_error", "❌ Ошибка при покупке достижения: {error}").format(error=result["reason"])
    
    await callback.answer()
    kb = back_to_achievements_keyboard(locale)
    
    await safe_edit_message(callback.message, text, reply_markup=kb)


async def process_secret_content(callback: types.CallbackQuery, locale):
    """Обработчик для раздела секретного контента"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Проверяем, покупал ли пользователь секретный контент
    has_video = has_purchased_secret(callback.from_user.id, SECRET_VIDEO_KEY)
    
    if has_video:
        text = locale.get("secret_content_text", "🔍 Секретный контент: {name}\n\n{content}").format(
            name=locale.get("secret_video_name", "Секретный ролик бубса"),
            content=SECRET_VIDEO_URL
        )
        kb = back_to_achievements_keyboard(locale)
    else:
        text = locale.get("buy_secret_text", "🔍 Выберите секретный контент для покупки:")
        kb = secret_content_keyboard(locale)
    
    try:
        await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await callback.message.answer(
            text=text,
            reply_markup=kb
        )
        logging.info("Sent new message as fallback")


async def process_buy_secret_video(callback: types.CallbackQuery, locale):
    """Обработчик для покупки секретного видео"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    text = locale.get("buy_secret_confirm", "Вы уверены, что хотите купить секретный контент \"{name}\" за {price} монет?").format(
        name=locale.get("secret_video_name", "Секретный ролик бубса"),
        price=SECRET_VIDEO_PRICE
    )
    kb = confirm_secret_purchase_keyboard(locale, SECRET_VIDEO_KEY)
    
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await callback.message.answer(
            text=text,
            reply_markup=kb
        )
        logging.info("Sent new message as fallback")


async def process_confirm_secret_purchase(callback: types.CallbackQuery, locale):
    """Обработчик для подтверждения покупки секретного контента"""
    locale = get_user_language(callback.from_user.id)
    
    # Получаем ключ контента из callback_data
    content_key = callback.data.split(":")[1]
    
    # Записываем покупку и выдаем достижение
    result = record_secret_purchase(callback.from_user.id, content_key, SECRET_VIDEO_PRICE)
    
    await callback.answer()
    
    if result["success"]:
        text = locale.get("buy_secret_success", "✅ Вы успешно приобрели секретный контент: {name}").format(
            name=locale.get("secret_video_name", "Секретный ролик бубса")
        )
        text += "\n\n" + locale.get("secret_content_text", "🔍 Секретный контент: {name}\n\n{content}").format(
            name=locale.get("secret_video_name", "Секретный ролик бубса"),
            content=SECRET_VIDEO_URL
        )
    else:
        if result["reason"] == "not_enough_coins":
            # Получаем текущий баланс пользователя
            db = SessionLocal()
            user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
            user_crystals = user.crystals if user else 0
            db.close()
            
            text = locale.get("buy_secret_not_enough_coins", "❌ Недостаточно монет. У вас {balance}, но нужно {price}").format(
                balance=user_crystals,
                price=SECRET_VIDEO_PRICE
            )
        elif result["reason"] == "already_purchased":
            text = locale.get("buy_secret_already_owned", "❌ Вы уже приобрели этот секретный контент")
        else:
            text = locale.get("buy_secret_error", "❌ Ошибка при покупке секретного контента: {error}").format(
                error=result["reason"]
            )
    
    kb = back_to_achievements_keyboard(locale)
    
    await safe_edit_message(callback.message, text, reply_markup=kb, disable_web_page_preview=False)


async def safe_edit_message(message, text, reply_markup=None, **kwargs):
    """
    Безопасно редактирует сообщение, обрабатывая ошибку MessageNotModified
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, **kwargs)
    except MessageNotModified:
        # Игнорируем ошибку, если сообщение не изменилось
        logging.info("Message not modified, ignoring")
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        try:
            await message.answer(text, reply_markup=reply_markup, **kwargs)
            logging.info("Sent new message as fallback")
        except Exception as e2:
            logging.error(f"Error sending fallback message: {e2}")


async def back_to_achievements(callback: types.CallbackQuery, locale):
    """Обработчик для кнопки 'Назад к достижениям'"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем количество достижений пользователя
    user_achievements = get_user_achievements(callback.from_user.id)
    total_achievements = len(ACHIEVEMENTS)
    count = len(user_achievements) if user_achievements else 0
    
    text = locale.get("achievements_text", "🏆 Ваши достижения: {count}/{total}").format(
        count=count, 
        total=total_achievements
    )
    kb = achievements_keyboard(locale)
    
    # Создаем новое сообщение вместо редактирования существующего
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb)


async def view_profile(callback: types.CallbackQuery, locale, state: FSMContext):
    """Обработчик для просмотра профиля пользователя"""
    user_id = int(callback.data.split(":")[1])
    announcement_type = callback.data.split(":")[2]
    await callback.answer()
    
    # Сохраняем текущий ID объявления в состоянии
    data = await state.get_data()
    current_announcement_id = None
    
    # Получаем текущий ID объявления из callback.message
    message_text = callback.message.caption or callback.message.text
    if message_text:
        try:
            # Пытаемся найти ID объявления в тексте сообщения
            import re
            match = re.search(r'ID: (\d+)', message_text)
            if match:
                current_announcement_id = int(match.group(1))
                # Сохраняем ID в нужном ключе состояния
                if announcement_type == "team":
                    await state.update_data(current_team_announcement_id=current_announcement_id)
                elif announcement_type == "club":
                    await state.update_data(current_club_announcement_id=current_announcement_id)
                elif announcement_type == "favorites":
                    # Для избранного нам не нужно сохранять ID, так как мы используем индекс
                    pass
        except Exception as e:
            logger.error(f"Error extracting announcement ID: {e}")
    
    db = SessionLocal()
    try:
        # Получаем информацию о пользователе
        user = db.query(User).filter(User.tg_id == user_id).first()
        if not user:
            await callback.message.answer(
                locale.get("user_not_found", "❌ Пользователь не найден"),
                reply_markup=profile_view_keyboard(locale, user_id, announcement_type)
            )
            return
        
        # Получаем достижения пользователя
        user_achievements = get_user_achievements(user_id)
        achievements_count = len(user_achievements) if user_achievements else 0
        
        # Формируем статус пользователя
        status = "👑 Premium" if user.is_premium else "👤 Обычный пользователь"
        
        # Формируем базовый текст профиля
        text = locale.get("profile_text", """
👤 Профиль пользователя

📝 ID: {user_id}
🏆 Достижений: {achievements_count}
🪙 Монет: {crystals}
📊 Статус: {status}
📅 Дата регистрации: {reg_date}""").format(
            user_id=user.tg_id,
            achievements_count=achievements_count,
            crystals=user.crystals,
            status=status,
            reg_date=user.created_at.strftime("%d.%m.%Y")
        )
        
        # Добавляем список достижений, если они есть
        if user_achievements:
            text += "\n\n📋 Список достижений:\n"
            for achievement in user_achievements:
                text += f"{achievement['icon']} {achievement['name']}\n"
        
        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=profile_view_keyboard(locale, user_id, announcement_type)
        )
    
    finally:
        db.close()


async def view_user_achievements(callback: types.CallbackQuery, locale):
    """Обработчик для просмотра достижений пользователя"""
    user_id = int(callback.data.split(":")[1])
    announcement_type = callback.data.split(":")[2]
    await callback.answer()
    
    # Получаем достижения пользователя
    user_achievements = get_user_achievements(user_id)
    
    if not user_achievements:
        text = locale.get("no_user_achievements", "🏅 У пользователя пока нет достижений.")
    else:
        text = locale.get("user_achievements_list", "📋 Достижения пользователя:") + "\n\n"
        
        for achievement in user_achievements:
            achieved_date = achievement['achieved_at'].strftime("%d.%m.%Y")
            text += f"{achievement['icon']} {achievement['name']} - {achievement['description']}\n"
            text += locale.get("achievement_date", "📅 Получено: {date}").format(date=achieved_date) + "\n\n"
    
    # Создаем клавиатуру с одной кнопкой "Назад"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_write", "✍️ Написать"), 
            url=f"tg://user?id={user_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_back", "🔙 Назад"), 
            callback_data=f"back_to_announcement:{announcement_type}"
        )
    )
    
    # Удаляем старое сообщение и отправляем новое
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb)


async def back_to_announcement(callback: types.CallbackQuery, locale, state: FSMContext):
    """Обработчик для возврата к объявлению"""
    announcement_type = callback.data.split(":")[1]
    await callback.answer()
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Получаем ID текущего объявления из состояния
    current_announcement_id = None
    if announcement_type == "team":
        current_announcement_id = data.get("current_team_announcement_id")
    elif announcement_type == "club":
        current_announcement_id = data.get("current_club_announcement_id")
    elif announcement_type == "favorites":
        favorite_index = data.get("favorite_index", 0)
        fav_list = get_favorites_list(callback.from_user.id)
        if fav_list and 0 <= favorite_index < len(fav_list):
            current_announcement_id = fav_list[favorite_index]
    
    if current_announcement_id:
        # Получаем объявление
        announcement = get_announcement_by_id(current_announcement_id)
        if announcement:
            # Получаем количество объявлений для определения has_next и has_prev
            count = get_announcements_count(announcement_type, callback.from_user.id)
            
            # Получаем текущий индекс объявления
            current_index = data.get("announcement_page", 0)
            
            # Определяем наличие следующих и предыдущих объявлений
            has_next = current_index < count - 1
            has_prev = current_index > 0
            
            # Формируем текст и клавиатуру
            text = display_announcement_with_keyword(announcement, locale)
            keyboard = announcement_keyboard(
                locale,
                announcement["id"],
                announcement["user_id"],
                has_next,
                has_prev,
                announcement_type
            )
            
            # Удаляем текущее сообщение
            await callback.message.delete()
            
            # Отправляем объявление заново
            await send_new_announcement_media(
                callback.message.bot,
                callback.from_user.id,
                announcement,
                text,
                keyboard
            )
            return
    
    # Если что-то пошло не так, возвращаемся в меню поиска
    from keyboards.inline_keyboard import search_team_menu_keyboard, search_club_menu_keyboard
    kb = search_team_menu_keyboard(locale) if announcement_type == "team" else search_club_menu_keyboard(locale)
    await callback.message.edit_text(
        locale.get("search_menu_text", "Выберите действие:"),
        reply_markup=kb
    )


def register_handlers_achievements(dp: Dispatcher, locale):
    """Регистрация всех обработчиков для достижений"""
    # Инициализируем достижения в базе данных
    initialize_achievements()
    
    # Регистрируем обработчики
    dp.register_callback_query_handler(
        lambda c: cmd_achievements(c, locale),
        lambda c: c.data == "achievements"
    )
    dp.register_callback_query_handler(
        lambda c: process_my_achievements(c, locale),
        lambda c: c.data == "my_achievements"
    )
    dp.register_callback_query_handler(
        lambda c: process_available_achievements(c, locale),
        lambda c: c.data == "available_achievements"
    )
    dp.register_callback_query_handler(
        lambda c: process_buy_achievement(c, locale),
        lambda c: c.data == "buy_achievement"
    )
    dp.register_callback_query_handler(
        lambda c: process_confirm_buy_achievement(c, locale),
        lambda c: c.data.startswith("confirm_buy_achievement:")
    )
    dp.register_callback_query_handler(
        lambda c: process_secret_content(c, locale),
        lambda c: c.data == "secret_content"
    )
    dp.register_callback_query_handler(
        lambda c: process_buy_secret_video(c, locale),
        lambda c: c.data == "buy_secret_video"
    )
    dp.register_callback_query_handler(
        lambda c: process_confirm_secret_purchase(c, locale),
        lambda c: c.data.startswith("confirm_secret_purchase:")
    )
    dp.register_callback_query_handler(
        lambda c: back_to_achievements(c, locale),
        lambda c: c.data == "back_to_achievements"
    )
    dp.register_callback_query_handler(
        lambda c, state: view_profile(c, locale, state),
        lambda c: c.data.startswith("view_profile:"),
        state="*"
    )
    dp.register_callback_query_handler(
        lambda c, state: back_to_announcement(c, locale, state),
        lambda c: c.data.startswith("back_to_announcement:"),
        state="*"
    )
    logging.info("Achievements handlers registered successfully") 