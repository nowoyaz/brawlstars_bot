from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from database.session import DATABASE_URL

def upgrade():
    engine = create_engine(DATABASE_URL)
    Base = declarative_base()
    
    # Добавляем колонку media_type
    engine.execute('ALTER TABLE announcements ADD COLUMN media_type VARCHAR DEFAULT "photo"')

def downgrade():
    engine = create_engine(DATABASE_URL)
    # Удаляем колонку media_type
    engine.execute('ALTER TABLE announcements DROP COLUMN media_type') 