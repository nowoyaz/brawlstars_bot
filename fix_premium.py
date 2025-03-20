from database.session import SessionLocal
from database.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_premium_status():
    session = SessionLocal()
    try:
        # Получаем всех пользователей
        users = session.query(User).all()
        
        # Сбрасываем премиум-статус для всех пользователей
        for user in users:
            if user.is_premium and not user.premium_until:
                logger.info(f"Сбрасываем премиум-статус для пользователя {user.tg_id}")
                user.is_premium = False
        
        session.commit()
        logger.info(f"Обработано пользователей: {len(users)}")
        
    except Exception as e:
        logger.error(f"Ошибка при исправлении премиум-статуса: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_premium_status() 