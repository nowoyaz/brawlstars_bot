import logging
from datetime import datetime, timezone
from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import save_announcement, get_user_language, is_user_premium
from keyboards.inline_keyboard import inline_main_menu_keyboard, action_announcement_keyboard, preview_announcement_keyboard, keyword_selection_keyboard

logger = logging.getLogger(__name__)

class AnnouncementStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_description = State()
    waiting_for_keyword = State()
    waiting_for_action = State()
    waiting_in_preview = State()

async def cmd_create_announcement(message: types.Message, announcement_type: str, locale, state: FSMContext):
    """Начало создания объявления"""
    locale = get_user_language(message.from_user.id)
    logger.info(locale["log_ann_start"].format(type=announcement_type, user=message.from_user.id))
    
    # Сбрасываем предыдущее состояние, если оно было
    await state.finish()
    
    # Начинаем новое состояние и сохраняем данные
    await state.update_data(announcement_type=announcement_type)
    await AnnouncementStates.waiting_for_photo.set()
    
    # Добавляем кнопку "Назад" в клавиатуру
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(locale["button_back"], callback_data="back_to_menu"))
    await message.answer(locale["ann_send_photo"], reply_markup=keyboard)

async def process_photo(message: types.Message, locale, state: FSMContext):
    """Обработка полученного медиа"""
    try:
        locale = get_user_language(message.from_user.id)
        logger.info(locale["log_ann_photo"].format(user=message.from_user.id))
        
        # Получаем текущие данные состояния
        data = await state.get_data()
        if not data.get('announcement_type'):
            await state.finish()
            await message.answer(locale["ann_cancelled"], reply_markup=inline_main_menu_keyboard(locale))
            return
        
        # Проверяем тип медиа
        is_premium = is_user_premium(message.from_user.id)
        has_valid_media = (
            message.photo or 
            (message.video and is_premium) or 
            (message.animation and is_premium)
        )
        
        if not has_valid_media:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(locale["button_back"], callback_data="back_to_menu"))
            await message.answer(locale["ann_media_invalid"], reply_markup=keyboard)
            return
        
        # Определяем тип медиа и получаем file_id
        if message.photo:
            media_id = message.photo[-1].file_id
            media_type = "photo"
        elif message.video and is_premium:
            media_id = message.video.file_id
            media_type = "video"
        elif message.animation and is_premium:
            media_id = message.animation.file_id
            media_type = "animation"
        else:
            await message.answer(locale["ann_media_invalid"])
            return
        
        # Сохраняем информацию о медиа
        await state.update_data(media_id=media_id, media_type=media_type)
        logger.info(locale["log_ann_media"].format(media_id=media_id, type=media_type))
        
        # Запрашиваем описание
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(locale["button_back"], callback_data="back_to_menu"))
        await message.answer(locale["ann_send_desc"], reply_markup=keyboard)
        await AnnouncementStates.waiting_for_description.set()
    except Exception as e:
        logger.error(f"Error in process_photo: {e}")
        await message.answer("An error occurred while processing media")

async def process_description(message: types.Message, locale, state: FSMContext):
    locale = get_user_language(message.from_user.id)
    description = message.text
    if len(description) < 20:
        await message.answer(locale["ann_desc_short"].format(count=len(description)))
        return
    
    # Сохраняем описание
    await state.update_data(description=description)
    data = await state.get_data()
    announcement_type = data.get("announcement_type")
    
    # Запрашиваем ключевое слово только для команд
    if announcement_type == "team":
        # Показываем клавиатуру с ключевыми словами
        await message.answer(locale["ann_select_keyword"], reply_markup=keyword_selection_keyboard(locale))
        await AnnouncementStates.waiting_for_keyword.set()
    else:
        # Для клубов сразу переходим к действию с публикацией
        await state.update_data(keyword=None)  # Явно устанавливаем keyword как None для клубов
        await message.answer(locale["ann_choose_action"], reply_markup=action_announcement_keyboard(locale))
        await AnnouncementStates.waiting_for_action.set()

async def process_keyword(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    keyword = None
    if callback.data != "skip_keyword":
        keyword = callback.data.replace("keyword_", "")
        # Отладочная информация
        print(f"Setting keyword for announcement: callback_data={callback.data}, extracted keyword={keyword}")
        
    await state.update_data(keyword=keyword)
    await callback.message.edit_text(locale["ann_choose_action"], reply_markup=action_announcement_keyboard(locale))
    await AnnouncementStates.waiting_for_action.set()

async def action_publish(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = await state.get_data()
    announcement_type = data.get("announcement_type")
    media_id = data.get("media_id")
    media_type = data.get("media_type", "photo")
    description = data.get("description")
    keyword = data.get("keyword")
    logger.info(locale["log_ann_publish"].format(user=callback.from_user.id))
    save_announcement(
        user_id=callback.from_user.id,
        announcement_type=announcement_type,
        image_id=media_id,
        description=description,
        keyword=keyword,
        media_type=media_type
    )
    await callback.message.edit_text(locale["ann_created_success"], reply_markup=inline_main_menu_keyboard(locale))
    await state.finish()

async def action_preview(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = await state.get_data()
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    description = data.get("description")
    keyword = data.get("keyword")
    preview_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    
    keyword_text = ""
    if keyword:
        keyword_display = locale.get(f"keyword_{keyword}", keyword)
        keyword_text = "\n" + locale["keyword_label"].format(keyword=keyword_display)
    
    # Добавляем премиум-метку, если пользователь премиум
    premium_text = ""
    if is_user_premium(callback.from_user.id):
        premium_text = " 🪙 PREMIUM"
    
    preview_text = f"<b>{description}</b>{keyword_text}{premium_text}\n\n🕒 {preview_date}"
    await callback.message.delete()
    
    # Отправляем медиа в зависимости от его типа
    if media_type == "photo":
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=media_id,
            caption=locale["ann_preview"] + "\n\n" + preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )
    elif media_type == "video":
        await callback.message.bot.send_video(
            chat_id=callback.from_user.id,
            video=media_id,
            caption=locale["ann_preview"] + "\n\n" + preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )
    else:  # animation (GIF)
        await callback.message.bot.send_animation(
            chat_id=callback.from_user.id,
            animation=media_id,
            caption=locale["ann_preview"] + "\n\n" + preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )
    
    await AnnouncementStates.waiting_in_preview.set()

async def preview_back(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.delete()
    await callback.message.bot.send_message(
        chat_id=callback.from_user.id,
        text=locale["ann_choose_action"],
        reply_markup=action_announcement_keyboard(locale)
    )
    await AnnouncementStates.waiting_for_action.set()

async def action_cancel(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer(locale["ann_cancel_popup"])
    await state.finish()
    await callback.message.edit_text(locale["ann_cancelled"], reply_markup=inline_main_menu_keyboard(locale))

async def show_preview(message: types.Message, locale, state: FSMContext):
    """Показывает предварительный просмотр объявления"""
    data = await state.get_data()
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    description = data.get("description")
    announcement_type = data.get("announcement_type")
    keyword = data.get("keyword") if announcement_type == "team" else None
    
    # Формируем текст превью
    preview_text = ""
    if announcement_type == "team" and keyword:
        preview_text += f"{locale['keyword_label'].format(keyword=locale.get(f'keyword_{keyword}', keyword))}\n"
    preview_text += description
    
    # Отправляем медиа в зависимости от его типа
    if media_type == "photo":
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=media_id,
            caption=preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )
    elif media_type == "video":
        await message.bot.send_video(
            chat_id=message.chat.id,
            video=media_id,
            caption=preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )
    else:  # animation (GIF)
        await message.bot.send_animation(
            chat_id=message.chat.id,
            animation=media_id,
            caption=preview_text,
            reply_markup=preview_announcement_keyboard(locale)
        )

async def back_to_menu(callback: types.CallbackQuery, locale, state: FSMContext):
    """Обработчик для кнопки "Назад" - возвращает в главное меню"""
    await callback.answer()
    await state.finish()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))

def register_announcement_handlers(dp: Dispatcher, locale):
    # Регистрируем обработчик для кнопки "Назад"
    dp.register_callback_query_handler(
        lambda call, state: back_to_menu(call, locale, state),
        lambda c: c.data == "back_to_menu",
        state="*"
    )
    
    # Регистрируем обработчики создания объявлений
    dp.register_callback_query_handler(
        lambda call, state: cmd_create_announcement(call.message, "team", locale, state),
        lambda c: c.data == "create_new_team",
        state="*"
    )
    dp.register_callback_query_handler(
        lambda call, state: cmd_create_announcement(call.message, "club", locale, state),
        lambda c: c.data == "create_new_club",
        state="*"
    )
    
    # Регистрируем обработчик медиа
    dp.register_message_handler(
        lambda message, state: process_photo(message, locale, state),
        content_types=[
            types.ContentType.PHOTO,
            types.ContentType.VIDEO,
            types.ContentType.ANIMATION
        ],
        state=AnnouncementStates.waiting_for_photo
    )
    
    # Остальные обработчики
    dp.register_message_handler(
        lambda message, state: process_description(message, locale, state),
        state=AnnouncementStates.waiting_for_description
    )
    dp.register_callback_query_handler(
        lambda call, state: process_keyword(call, locale, state),
        lambda c: c.data.startswith("keyword_") or c.data == "skip_keyword",
        state=AnnouncementStates.waiting_for_keyword
    )
    dp.register_callback_query_handler(
        lambda call, state: action_publish(call, locale, state),
        lambda c: c.data == "publish_announcement",
        state=AnnouncementStates.waiting_for_action
    )
    dp.register_callback_query_handler(
        lambda call, state: action_preview(call, locale, state),
        lambda c: c.data == "preview_announcement",
        state=AnnouncementStates.waiting_for_action
    )
    dp.register_callback_query_handler(
        lambda call, state: action_cancel(call, locale, state),
        lambda c: c.data == "cancel_announcement",
        state=AnnouncementStates.waiting_for_action
    )
    dp.register_callback_query_handler(
        lambda call, state: preview_back(call, locale, state),
        lambda c: c.data == "preview_back",
        state=AnnouncementStates.waiting_in_preview
    )
