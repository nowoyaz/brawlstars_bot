import logging
from sqlalchemy.orm import Session
from aiogram import types
from database.session import SessionLocal
from database.models import User
from utils.achievements import check_and_award_achievements
from .locale import locale

async def track_section_visit(callback: types.CallbackQuery, section_name: str):
    try:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_id == callback.from_user.id).first()
            if not user:
                return
            
            # Инициализируем список посещенных разделов, если он пустой
            if user.visited_sections is None:
                user.visited_sections = []
            
            # Добавляем новый раздел, если его еще нет в списке
            if section_name not in user.visited_sections:
                user.visited_sections.append(section_name)
                db.commit()
                
                # Проверяем достижения
                new_achievements = await check_and_award_achievements(user.user_id)
                if new_achievements:
                    for achievement in new_achievements:
                        await callback.message.answer(
                            locale["new_achievement"].format(
                                emoji=achievement["emoji"],
                                name=achievement["name"],
                                description=achievement["description"]
                            )
                        )
                        
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error in track_section_visit: {e}")

async def process_menu_navigation(callback: types.CallbackQuery, locale):
    section = callback.data
    await track_section_visit(callback, section)
    # ... остальной код обработки навигации по меню ... 