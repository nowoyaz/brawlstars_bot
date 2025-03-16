from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.helpers import get_user_language, is_user_premium
from keyboards.inline_keyboard import inline_main_menu_keyboard
from database.session import SessionLocal
from database.models import User
from database.achievements import get_user_achievements

async def show_profile(callback: types.CallbackQuery, locale):
    """Показывает профиль пользователя"""
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    session = SessionLocal()
    user = session.query(User).filter(User.tg_id == callback.from_user.id).first()
    
    # Если пользователя нет в базе, создаем его
    if not user:
        user = User(
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            language='ru',
            crystals=0
        )
        session.add(user)
        session.commit()
    
    # Получаем достижения пользователя
    user_achievements = get_user_achievements(user.tg_id)
    achievements_count = len(user_achievements) if user_achievements else 0
    
    # Формируем статус пользователя
    status = locale.get("premium_status_active") if is_user_premium(user.tg_id) else locale.get("premium_status_inactive")
    
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
    
    session.close()
    
    # Отправляем сообщение с профилем
    await callback.message.edit_text(
        text,
        reply_markup=inline_main_menu_keyboard(locale)
    )

def register_profile_handlers(dp: Dispatcher, locale):
    """Регистрация обработчиков профиля"""
    dp.register_callback_query_handler(
        lambda call: show_profile(call, locale),
        lambda c: c.data == "profile"
    ) 