import datetime
from sqlalchemy import select, update
from database.models import User, PremiumPrice
from database.session import SessionLocal

def update_user_premium(user_id: int, end_date: datetime.datetime):
    """Обновляет премиум статус пользователя.
    
    Args:
        user_id (int): ID пользователя
        end_date (datetime.datetime): Дата окончания премиума
    """
    session = SessionLocal()
    try:
        # Получаем пользователя
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        # Обновляем премиум статус
        user.is_premium = True
        user.premium_end_date = end_date
        
        session.commit()
        return user
    finally:
        session.close()

def get_premium_prices():
    """Получает все цены для разных типов подписки"""
    session = SessionLocal()
    try:
        prices = session.query(PremiumPrice).all()
        
        # Если цен нет в базе, создаем значения по умолчанию
        if not prices:
            default_prices = [
                PremiumPrice(duration_type="month", price=500),  # 1 месяц
                PremiumPrice(duration_type="half_year", price=2500),  # 6 месяцев
                PremiumPrice(duration_type="year", price=4500),  # 1 год
                PremiumPrice(duration_type="forever", price=9900)  # навсегда
            ]
            
            for price in default_prices:
                session.add(price)
            
            session.commit()
            
            # Повторно запрашиваем цены после добавления
            prices = session.query(PremiumPrice).all()
        
        return prices
    finally:
        session.close()

def update_premium_price(duration_type: str, new_price: int):
    """Обновляет цену для указанного типа подписки"""
    session = SessionLocal()
    try:
        # Ищем запись с указанным типом подписки
        price = session.query(PremiumPrice).filter(PremiumPrice.duration_type == duration_type).first()
        
        if price:
            # Обновляем существующую запись
            price.price = new_price
            price.updated_at = datetime.datetime.now()
        else:
            # Создаем новую запись
            new_price_record = PremiumPrice(
                duration_type=duration_type,
                price=new_price
            )
            session.add(new_price_record)
        
        session.commit()
        return True
    finally:
        session.close() 