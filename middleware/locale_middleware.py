import json
import os
from aiogram.dispatcher.middlewares import BaseMiddleware
from database.session import SessionLocal
from database.models import User
import logging

logger = logging.getLogger(__name__)

async def get_user_locale(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        return user.language if user else 'ru'
    except Exception as e:
        logger.error(f"Error getting user locale: {e}")
        return 'ru'
    finally:
        session.close()

class LocaleMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update, data):
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        # Если не удалось определить user_id – используем язык по умолчанию
        lang = "ru"
        if user_id is not None:
            lang = await get_user_locale(user_id)
        locale_path = os.path.join("locale", f"{lang}.json")
        try:
            with open(locale_path, encoding="utf-8") as f:
                data["locale"] = json.load(f)
        except Exception as e:
            # В случае ошибки грузим язык по умолчанию
            with open(os.path.join("locale", "ru.json"), encoding="utf-8") as f:
                data["locale"] = json.load(f)
