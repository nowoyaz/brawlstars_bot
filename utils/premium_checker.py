import datetime
from sqlalchemy import select
from database.models import User
from database.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

async def check_premium_status():
    """Проверяет и обновляет премиум статус пользователей."""
    try:
        session = SessionLocal()
        # Получаем всех премиум пользователей
        stmt = select(User).where(
            User.is_premium == True,
            User.premium_end_date <= datetime.datetime.now()
        )
        result = session.execute(stmt)
        expired_users = result.scalars().all()
        
        # Обновляем статус для пользователей с истекшим премиумом
        for user in expired_users:
            user.is_premium = False
            logger.info(f"Премиум статус пользователя {user.id} истек")
        
        session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке премиум статуса: {str(e)}")

async def schedule_premium_check(dp):
    """Запускает периодическую проверку премиум статуса."""
    import asyncio
    while True:
        await check_premium_status()
        await asyncio.sleep(3600)  # Проверяем каждый час 