from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, PremiumPrice
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Инициализируем цены по умолчанию
    session = SessionLocal()
    try:
        PremiumPrice.initialize_default_prices(session)
    finally:
        session.close()
