import logging
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import save_announcement, get_user_language
from keyboards.inline_keyboard import inline_main_menu_keyboard, action_announcement_keyboard, preview_announcement_keyboard

logger = logging.getLogger(__name__)

class AnnouncementStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_description = State()
    waiting_for_action = State()
    waiting_in_preview = State()

async def cmd_create_announcement(message: types.Message, announcement_type: str, locale, state: FSMContext):
    locale = get_user_language(message.from_user.id)
    logger.info("Начало создания объявления: type=%s, user=%s", announcement_type, message.from_user.id)
    await state.update_data(announcement_type=announcement_type)
    await message.answer(locale["ann_send_photo"])
    await AnnouncementStates.waiting_for_photo.set()

async def process_photo(message: types.Message, locale, state: FSMContext):
    locale = get_user_language(message.from_user.id)
    logger.info("Получено фото от user=%s", message.from_user.id)
    if not message.photo:
        await message.answer(locale["ann_photo_invalid"])
        return
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    logger.info("Сохранён photo_id=%s", photo_id)
    await message.answer(locale["ann_send_desc"])
    await AnnouncementStates.waiting_for_description.set()

async def process_description(message: types.Message, locale, state: FSMContext):
    locale = get_user_language(message.from_user.id)
    logger.info("Получено описание от user=%s", message.from_user.id)
    description = message.text
    if len(description) < 20:
        await message.answer(locale["ann_desc_short"].format(count=len(description)))
        return
    await state.update_data(description=description)
    await message.answer(locale["ann_choose_action"], reply_markup=action_announcement_keyboard(locale))
    await AnnouncementStates.waiting_for_action.set()

async def action_publish(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = await state.get_data()
    announcement_type = data.get("announcement_type")
    photo_id = data.get("photo_id")
    description = data.get("description")
    logger.info("Публикация объявления от user=%s", callback.from_user.id)
    save_announcement(
        user_id=callback.from_user.id,
        announcement_type=announcement_type,
        image_id=photo_id,
        description=description
    )
    await callback.message.edit_text(locale["ann_created_success"], reply_markup=inline_main_menu_keyboard(locale))
    await state.finish()

async def action_preview(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    data = await state.get_data()
    photo_id = data.get("photo_id")
    description = data.get("description")
    preview_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    preview_text = f"<b>{description}</b>\n\n🕒 {preview_date}"
    await callback.message.delete()
    await callback.message.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=photo_id,
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
    await callback.answer("Создание объявления отменено")
    await state.finish()
    await callback.message.edit_text(locale["ann_cancelled"], reply_markup=inline_main_menu_keyboard(locale))

def register_announcement_handlers(dp: Dispatcher, locale):
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
    dp.register_message_handler(
        lambda message, state: process_photo(message, locale, state),
        content_types=types.ContentTypes.PHOTO,
        state=AnnouncementStates.waiting_for_photo
    )
    dp.register_message_handler(
        lambda message, state: process_description(message, locale, state),
        state=AnnouncementStates.waiting_for_description
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
