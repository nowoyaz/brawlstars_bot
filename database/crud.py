import datetime
from sqlalchemy import select
from database.models import User
from database.session import async_session

async def update_user_premium(user_id: int, end_date: datetime.datetime):
    """Обновляет премиум статус пользователя.
    
    Args:
        user_id (int): ID пользователя
        end_date (datetime.datetime): Дата окончания премиума
    """
    async with async_session() as session:
        # Получаем пользователя
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        # Обновляем премиум статус
        user.is_premium = True
        user.premium_end_date = end_date
        
        await session.commit()
        return user 