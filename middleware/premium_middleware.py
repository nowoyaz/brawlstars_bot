from aiogram.dispatcher.middlewares import BaseMiddleware
from database.session import SessionLocal
from database.models import User

class PremiumMiddleware(BaseMiddleware):
    async def on_process_message(self, message, data):
        session = SessionLocal()
        user = session.query(User).filter(User.id == message.from_user.id).first()
        session.close()
        data["is_premium"] = user.is_premium if user else False