from sqlalchemy import create_engine
from database.session import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    engine = create_engine(DATABASE_URL)
    try:
        # Создаем временную таблицу
        engine.execute('''
            CREATE TABLE IF NOT EXISTS promo_uses_new (
                id INTEGER PRIMARY KEY,
                promo_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (promo_id) REFERENCES promo_codes (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Копируем данные из старой таблицы в новую, используя правильные user_id
        engine.execute('''
            INSERT INTO promo_uses_new (promo_id, user_id, used_at)
            SELECT pu.promo_id, u.id, pu.used_at
            FROM promo_uses pu
            JOIN users u ON u.tg_id = pu.user_id
        ''')
        
        # Удаляем старую таблицу
        engine.execute('DROP TABLE promo_uses')
        
        # Переименовываем новую таблицу
        engine.execute('ALTER TABLE promo_uses_new RENAME TO promo_uses')
        
        # Создаем индексы
        engine.execute('CREATE INDEX IF NOT EXISTS idx_promo_uses_promo_id ON promo_uses (promo_id)')
        engine.execute('CREATE INDEX IF NOT EXISTS idx_promo_uses_user_id ON promo_uses (user_id)')
        
        logger.info("Миграция promo_uses успешно завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении миграции: {str(e)}")
        raise

if __name__ == "__main__":
    upgrade()