from sqlalchemy import create_engine, BigInteger
from sqlalchemy.sql import text
from config import DATABASE_URL

def migrate():
    # Создаем движок для подключения к базе данных
    engine = create_engine(DATABASE_URL.replace('+asyncpg', ''))
    
    # Изменяем тип колонок на BIGINT
    with engine.connect() as connection:
        # Изменяем тип id и tg_id в таблице users
        connection.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN id TYPE BIGINT,
            ALTER COLUMN tg_id TYPE BIGINT;
        """))
        
        # Изменяем тип referrer_id и referred_id в таблице referrals
        connection.execute(text("""
            ALTER TABLE referrals 
            ALTER COLUMN referrer_id TYPE BIGINT,
            ALTER COLUMN referred_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_id в таблице announcements
        connection.execute(text("""
            ALTER TABLE announcements 
            ALTER COLUMN user_id TYPE BIGINT;
        """))
        
        # Изменяем тип reporter_id в таблице reports
        connection.execute(text("""
            ALTER TABLE reports 
            ALTER COLUMN reporter_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_id в таблице favorites
        connection.execute(text("""
            ALTER TABLE favorites 
            ALTER COLUMN user_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_id в таблице user_achievements
        connection.execute(text("""
            ALTER TABLE user_achievements 
            ALTER COLUMN user_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_id в таблице user_visited_sections
        connection.execute(text("""
            ALTER TABLE user_visited_sections 
            ALTER COLUMN user_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_id в таблице user_secret_purchases
        connection.execute(text("""
            ALTER TABLE user_secret_purchases 
            ALTER COLUMN user_id TYPE BIGINT;
        """))
        
        # Изменяем тип user_tg_id в таблице user_sponsor_subscriptions
        connection.execute(text("""
            ALTER TABLE user_sponsor_subscriptions 
            ALTER COLUMN user_tg_id TYPE BIGINT;
        """))
        
        connection.commit()

if __name__ == "__main__":
    migrate() 