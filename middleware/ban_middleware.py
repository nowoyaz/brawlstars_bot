from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from database.session import SessionLocal
from database.models import User

class BanMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update, data):
        # Определяем user_id в зависимости от типа обновления
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        if user_id is None:
            return
        session = SessionLocal()
        user = session.query(User).filter(User.id == user_id).first()
        session.close()
        if user and user.blocked:
            # Опционально: можно отправить уведомление заблокированному пользователю
            # Например:
            # if update.message:
            #     await update.message.answer("Вы заблокированы.")
            # elif update.callback_query:
            #     await update.callback_query.answer("Вы заблокированы.", show_alert=True)
            raise CancelHandler()
