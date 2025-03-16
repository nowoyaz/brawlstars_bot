from aiogram.dispatcher.middlewares import BaseMiddleware
from database.session import SessionLocal
from database.models import User
from aiogram import types
import logging

logger = logging.getLogger(__name__)

class PremiumMiddleware(BaseMiddleware):
    async def on_process_message(self, message, data):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == message.from_user.id).first()
            data["is_premium"] = user.is_premium if user else False
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
            data["is_premium"] = False
        finally:
            session.close()

async def check_premium(message: types.Message):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == message.from_user.id).first()
        return user.is_premium if user else False
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
        return False
    finally:
        session.close()