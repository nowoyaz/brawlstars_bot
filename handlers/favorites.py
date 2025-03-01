from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import get_favorites_list, get_announcement_by_id, get_announcements_count, get_user_language
from keyboards.inline_keyboard import announcement_keyboard, inline_main_menu_keyboard
from aiogram.types import InputMediaPhoto

# FSM для избранного (для хранения текущего индекса)
class FavoritesStates(StatesGroup):
    favorite_index = State()

# Обработчик для показа избранного – вызывается при нажатии на кнопку "Избранное"
async def cmd_favorites(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    fav_list = get_favorites_list(callback.from_user.id)
    if not fav_list:
        await callback.message.edit_text("💔 Избранных объявлений нет", reply_markup=inline_main_menu_keyboard(locale))
        return
    # Устанавливаем индекс в 0
    await state.update_data(favorite_index=0)
    announcement_id = fav_list[0]
    announcement = get_announcement_by_id(announcement_id)
    if announcement:
        count = len(fav_list)
        has_next = count > 1
        premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
        media = InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.edit_media(media, reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "favorites"))
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

# Обработчик для кнопки "Дальше" в разделе избранного
async def process_next_favorite(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    fav_list = get_favorites_list(callback.from_user.id)
    if not fav_list:
        await callback.message.edit_text("💔 Избранных объявлений нет", reply_markup=inline_main_menu_keyboard(locale))
        return
    data = await state.get_data()
    favorite_index = data.get("favorite_index", 0)
    count = len(fav_list)
    next_index = (favorite_index + 1) % count
    await state.update_data(favorite_index=next_index)
    announcement_id = fav_list[favorite_index]
    announcement = get_announcement_by_id(announcement_id)
    if announcement:
        premium_label = " 💎 PREMIUM" if announcement.get("is_premium") else ""
        text = f"{announcement['description']}{premium_label}\n\n🕒 {announcement['created_at']}"
        has_next = count > 1
        try:
            await callback.message.delete()
        except Exception:
            pass
        media = InputMediaPhoto(announcement["image_id"], caption=text)
        await callback.message.bot.send_photo(
            callback.from_user.id,
            photo=announcement["image_id"],
            caption=text,
            reply_markup=announcement_keyboard(locale, announcement["id"], announcement["user_id"], has_next, "favorites")
        )
    else:
        await callback.message.edit_text("Объявление не найдено", reply_markup=inline_main_menu_keyboard(locale))

async def process_remove_favorite(callback: types.CallbackQuery, locale, state: FSMContext):
    locale = get_user_language(callback.from_user.id)
    await callback.answer("Удалено из избранного")
    data = callback.data.split(":")
    if len(data) >= 3:
        announcement_id = int(data[1])
        # Удаляем избранное
        from utils.helpers import remove_favorite
        remove_favorite(callback.from_user.id, announcement_id)
    # После удаления обновляем список избранного
    await cmd_favorites(callback, locale, state)

def register_handlers_favorites(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call, state: cmd_favorites(call, locale, state), lambda c: c.data == "favorites")
    dp.register_callback_query_handler(lambda call, state: process_next_favorite(call, locale, state), lambda c: c.data == "next:favorites")
    dp.register_callback_query_handler(lambda call, state: process_remove_favorite(call, locale, state), lambda c: c.data.startswith("favorite:") and "favorites" in c.data)
