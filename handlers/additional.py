from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.inline_keyboard import additional_keyboard, inline_main_menu_keyboard
from utils.helpers import get_user_announcements_count, get_referral_count, is_user_premium, can_receive_daily_crystals, give_daily_crystals
from utils.helpers import get_user_language, record_section_visit

# Обработчик для раздела "Дополнительно"
async def cmd_additional(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Записываем посещение раздела
    record_section_visit(callback.from_user.id, "additional")
    
    text = locale["additional_text"]
    kb = additional_keyboard(locale)
    await callback.message.edit_text(text, reply_markup=kb)



async def process_announcement_count(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Проверяем, является ли пользователь премиум
    if not is_user_premium(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Эта функция доступна только для премиум-пользователей",
            reply_markup=inline_main_menu_keyboard(locale)
        )
        return
    
    # Получаем общее количество всех объявлений в базе данных
    from database.session import SessionLocal
    from database.models import Announcement
    
    session = SessionLocal()
    
    # Количество объявлений типа "team"
    team_count = session.query(Announcement).filter(
        Announcement.announcement_type == "team"
    ).count()
    
    # Количество объявлений типа "club"
    club_count = session.query(Announcement).filter(
        Announcement.announcement_type == "club"
    ).count()
    
    # Общее количество объявлений
    total = team_count + club_count
    
    session.close()
    
    text = locale["announcement_count_text"].format(
        team=team_count, 
        club=club_count, 
        total=total
    )
    
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))



async def process_referral_program(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    # Формируем реферальную ссылку (замените YourBotUsername на имя вашего бота)
    referral_link = f"https://t.me/Bubser_PoiskBot?start={callback.from_user.id}"
    count = get_referral_count(callback.from_user.id)
    text = locale["referral_text"].format(referral_link=referral_link, count=count)
    await callback.message.edit_text(text, reply_markup=inline_main_menu_keyboard(locale))


# Обработчик для кнопки "Назад" – возвращает в главное меню
async def process_additional_back(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(locale["menu_text"], reply_markup=inline_main_menu_keyboard(locale))


async def process_daily_crystals(callback: types.CallbackQuery, locale):
    """Обработчик для получения ежедневных кристаллов"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    if can_receive_daily_crystals(callback.from_user.id):
        success, amount = give_daily_crystals(callback.from_user.id)
        if success:
            await callback.message.edit_text(
                locale["daily_crystals_received"].format(amount=amount),
                reply_markup=inline_main_menu_keyboard(locale)
            )
        else:
            await callback.message.edit_text(
                locale["daily_crystals_error"],
                reply_markup=inline_main_menu_keyboard(locale)
            )
    else:
        await callback.message.edit_text(
            locale["daily_crystals_already"],
            reply_markup=inline_main_menu_keyboard(locale)
        )

def register_handlers_additional(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_additional(call, locale), lambda c: c.data == "additional")
    dp.register_callback_query_handler(lambda call: process_announcement_count(call, locale), lambda c: c.data == "announcement_count")
    dp.register_callback_query_handler(lambda call: process_referral_program(call, locale), lambda c: c.data == "referral")
    dp.register_callback_query_handler(lambda call: process_additional_back(call, locale), lambda c: c.data == "back_to_main")
    dp.register_callback_query_handler(
        lambda c: process_daily_crystals(c, locale),
        text="daily_crystals"
    )
