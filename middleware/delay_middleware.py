import asyncio
from aiogram.dispatcher.middlewares import BaseMiddleware
from database.session import SessionLocal
from database.models import User

class DelayMiddleware(BaseMiddleware):
    async def on_process_message(self, message, data):
        session = SessionLocal()
        user = session.query(User).filter(User.id == message.from_user.id).first()
        session.close()
        if not user or not user.is_premium:
            await asyncio.sleep(1.5)
