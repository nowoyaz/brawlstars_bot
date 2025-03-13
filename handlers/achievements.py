import logging
from aiogram import types
from database.session import SessionLocal
from database.models import User
from utils.achievements import format_achievements_message, check_and_award_achievements
from keyboards.inline_keyboard import additional_keyboard

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
                    reply_markup=additional_keyboard(locale)
                )
                logging.info("Message edited successfully")
            except Exception as e:
                logging.error(f"Error editing message: {e}")
                await callback.message.answer(
                    text=message,
                    reply_markup=additional_keyboard(locale)
                )
                logging.info("Sent new message as fallback")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Global error in show_achievements: {e}")

def register_handlers_achievements(dp, locale):
    """Регистрация обработчиков достижений"""
    logging.info("Starting achievements handlers registration")
    
    async def achievements_callback(c: types.CallbackQuery):
        logging.info("Achievement callback triggered")
        await show_achievements(c, locale)
    
    dp.register_callback_query_handler(
        achievements_callback,
        lambda c: c.data == "achievements",  # Используем lambda вместо text
        state="*"
    )
    logging.info("Achievements handlers registered successfully") 