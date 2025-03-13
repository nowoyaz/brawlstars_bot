import datetime
from sqlalchemy import select, update, desc, or_, func
from database.models import User, PremiumPrice, Sponsor, UserSponsorSubscription
from database.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

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
                PremiumPrice(duration_days=30, price=500),  # 1 месяц
                PremiumPrice(duration_days=180, price=2500),  # 6 месяцев
                PremiumPrice(duration_days=365, price=4500),  # 1 год
                PremiumPrice(duration_days=9999, price=9900)  # навсегда
            ]
            
            for price in default_prices:
                session.add(price)
            
            session.commit()
            
            # Повторно запрашиваем цены после добавления
            prices = session.query(PremiumPrice).all()
        
        return prices
    finally:
        session.close()

def update_premium_price(duration_days: int, new_price: float):
    """Обновляет цену для указанного периода подписки"""
    session = SessionLocal()
    try:
        # Ищем запись с указанным периодом подписки
        price = session.query(PremiumPrice).filter(PremiumPrice.duration_days == duration_days).first()
        
        if price:
            # Обновляем существующую запись
            price.price = new_price
            price.updated_at = datetime.datetime.now()
        else:
            # Создаем новую запись
            new_price_record = PremiumPrice(
                duration_days=duration_days,
                price=new_price
            )
            session.add(new_price_record)
        
        session.commit()
        return True
    finally:
        session.close()

# Функции для работы со спонсорами
def get_sponsors(only_active=True):
    """Получает список спонсоров"""
    session = SessionLocal()
    try:
        query = session.query(Sponsor)
        if only_active:
            query = query.filter(Sponsor.is_active == True)
        sponsors = query.all()
        return sponsors
    finally:
        session.close()

def get_sponsor_by_id(sponsor_id: int):
    """Получить спонсора по ID"""
    session = SessionLocal()
    try:
        return session.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
    finally:
        session.close()

def add_sponsor(name: str, link: str, reward: int = 10, channel_id: str = None):
    """Добавляет нового спонсора"""
    session = SessionLocal()
    try:
        sponsor = Sponsor(
            name=name,
            link=link,
            reward=reward,
            channel_id=channel_id
        )
        session.add(sponsor)
        session.commit()
        return sponsor
    finally:
        session.close()

def update_sponsor(sponsor_id: int, name: str = None, link: str = None, reward: int = None, channel_id: str = None, is_active: bool = None):
    """Обновляет данные спонсора"""
    session = SessionLocal()
    try:
        sponsor = session.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
        if not sponsor:
            return False
            
        if name is not None:
            sponsor.name = name
        if link is not None:
            sponsor.link = link
        if reward is not None:
            sponsor.reward = reward
        if channel_id is not None:
            sponsor.channel_id = channel_id
        if is_active is not None:
            sponsor.is_active = is_active
            
        session.commit()
        return True
    finally:
        session.close()

def delete_sponsor(sponsor_id: int):
    """Удаляет спонсора"""
    session = SessionLocal()
    try:
        sponsor = session.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
        if not sponsor:
            return False
        
        # Удаляем все подписки пользователей на этого спонсора
        session.query(UserSponsorSubscription).filter(UserSponsorSubscription.sponsor_id == sponsor_id).delete()
            
        session.delete(sponsor)
        session.commit()
        return True
    finally:
        session.close()

def check_user_subscription(user_id: int, sponsor_id: int = None):
    """Проверяет подписки пользователя на спонсоров"""
    session = SessionLocal()
    try:
        query = session.query(UserSponsorSubscription).filter(UserSponsorSubscription.user_tg_id == user_id)
        
        if sponsor_id:
            query = query.filter(UserSponsorSubscription.sponsor_id == sponsor_id)
            return query.first() is not None
        
        return query.all()
    finally:
        session.close()

def add_user_subscription(user_id: int, sponsor_id: int):
    """Добавляет подписку пользователя на спонсора"""
    session = SessionLocal()
    try:
        # Проверяем, существует ли уже такая подписка
        subscription = session.query(UserSponsorSubscription).filter(
            UserSponsorSubscription.user_tg_id == user_id,
            UserSponsorSubscription.sponsor_id == sponsor_id
        ).first()
        
        if subscription:
            return subscription
        
        # Создаем новую подписку
        subscription = UserSponsorSubscription(user_tg_id=user_id, sponsor_id=sponsor_id)
        session.add(subscription)
        session.commit()
        return subscription
    finally:
        session.close()

def remove_user_subscription(user_id: int, sponsor_id: int):
    """Удаляет подписку пользователя на спонсора"""
    session = SessionLocal()
    try:
        subscription = session.query(UserSponsorSubscription).filter(
            UserSponsorSubscription.user_tg_id == user_id,
            UserSponsorSubscription.sponsor_id == sponsor_id
        ).first()
        
        if not subscription:
            return False
        
        session.delete(subscription)
        session.commit()
        return True
    finally:
        session.close()

def get_user_by_id(user_id: int):
    """Получает пользователя по его Telegram ID"""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.tg_id == user_id).first()
    finally:
        session.close()

def add_coins_to_user(user_id: int, coins: int):
    """Добавляет монеты пользователю"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
        
        user.coins += coins
        session.commit()
        return True
    finally:
        session.close() 