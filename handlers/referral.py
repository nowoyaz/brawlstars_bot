import logging
from aiogram import types
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database.models import User
from utils.achievements import check_and_award_achievements

async def process_referral(message: types.Message, referrer_id: int, locale):
    try:
        db = SessionLocal()
        try:
            # Проверяем существование реферера
            referrer = db.query(User).filter(User.user_id == referrer_id).first()
            if not referrer:
                await message.answer(locale["error_referrer_not_found"])
                return
                
            # Увеличиваем счетчик рефералов
            referrer.referral_count = (referrer.referral_count or 0) + 1
            db.commit()
            
            # Проверяем достижения реферера
            new_achievements = await check_and_award_achievements(referrer.user_id)
            if new_achievements:
                # Уведомляем реферера о новых достижениях
                for achievement in new_achievements:
                    try:
                        await message.bot.send_message(
                            referrer.user_id,
                            locale["new_achievement"].format(
                                emoji=achievement["emoji"],
                                name=achievement["name"],
                                description=achievement["description"]
                            )
                        )
                    except Exception as e:
                        logging.error(f"Error sending achievement notification to referrer: {e}")
            
            # Отправляем уведомление рефереру
            try:
                await message.bot.send_message(
                    referrer.user_id,
                    locale["new_referral_notification"].format(user_id=message.from_user.id)
                )
            except Exception as e:
                logging.error(f"Error sending referral notification: {e}")
                
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error in process_referral: {e}")
        await message.answer(locale["error_general"]) 