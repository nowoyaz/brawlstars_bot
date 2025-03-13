from sqlalchemy import create_engine
from database.session import DATABASE_URL

def upgrade():
    engine = create_engine(DATABASE_URL)
    
    # Создаем таблицы для промокодов
    engine.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY,
            code VARCHAR NOT NULL UNIQUE,
            duration_days INTEGER NOT NULL,
            max_uses INTEGER DEFAULT 1,
            uses_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT NULL
        )
    ''')
    
    engine.execute('''
        CREATE TABLE IF NOT EXISTS promo_uses (
            id INTEGER PRIMARY KEY,
            promo_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (promo_id) REFERENCES promo_codes (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Создаем индексы для оптимизации запросов
    engine.execute('CREATE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes (code)')
    engine.execute('CREATE INDEX IF NOT EXISTS idx_promo_uses_promo_id ON promo_uses (promo_id)')
    engine.execute('CREATE INDEX IF NOT EXISTS idx_promo_uses_user_id ON promo_uses (user_id)')

if __name__ == "__main__":
    upgrade()
    print("Promo codes migration completed successfully") 