from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base, PremiumPrice
from config import DATABASE_URL

# Создаем асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Создаем фабрику асинхронных сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Функция для получения асинхронной сессии
async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Инициализируем цены по умолчанию
    session = SessionLocal()
    try:
        PremiumPrice.initialize_default_prices(session)
    finally:
        session.close()
