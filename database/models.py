import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()




class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, unique=True, index=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    premium_end_date = Column(DateTime, nullable=True)
    crystals = Column(Integer, default=100)
    language = Column(String, default="ru")
    blocked = Column(Boolean, default=False)
    last_gift = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    coins = Column(Integer, default=0)
    premium_until = Column(DateTime, nullable=True)

    # Обратная связь с подписками пользователя на спонсоров
    sponsor_subscriptions = relationship("UserSponsorSubscription", back_populates="user", foreign_keys="UserSponsorSubscription.user_tg_id")

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, nullable=False)
    referred_id = Column(Integer, nullable=False, unique=True)  # каждый реферал может быть только один раз
    created_at = Column(DateTime, default=datetime.datetime.utcnow)



class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    announcement_type = Column(Enum("team", "club", name="announcement_type"), nullable=False)
    image_id = Column(String, nullable=False)
    media_id = Column(String, nullable=True)
    media_type = Column(String, default="photo")
    description = Column(Text, nullable=False)
    keyword = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    announcement_id = Column(Integer, ForeignKey("announcements.id"))
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    announcement_id = Column(Integer, ForeignKey("announcements.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CrystalTransaction(Base):
    __tablename__ = "crystal_transactions"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PremiumPrice(Base):
    __tablename__ = "premium_prices"
    id = Column(Integer, primary_key=True, index=True)
    duration_days = Column(Integer, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __init__(self, duration_days=None, price=None):
        super().__init__()
        self.duration_days = duration_days
        self.price = price

    @classmethod
    def initialize_default_prices(cls, session):
        """Инициализирует цены по умолчанию, если их нет"""
        default_prices = [
            {"duration_days": 30, "price": 500.0},    # месяц
            {"duration_days": 180, "price": 2500.0},  # полгода
            {"duration_days": 365, "price": 4500.0},  # год
            {"duration_days": 36500, "price": 9900.0} # навсегда
        ]
        
        for price_data in default_prices:
            existing = session.query(cls).filter_by(duration_days=price_data["duration_days"]).first()
            if not existing:
                new_price = cls(duration_days=price_data["duration_days"], price=price_data["price"])
                session.add(new_price)
        
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    channel_id = Column(String, nullable=True)  # ID канала для проверки подписки
    reward = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Обратная связь с подписками пользователей
    user_subscriptions = relationship("UserSponsorSubscription", back_populates="sponsor")

class UserSponsorSubscription(Base):
    __tablename__ = 'user_sponsor_subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_tg_id = Column(Integer, ForeignKey('users.tg_id'), nullable=False)
    sponsor_id = Column(Integer, ForeignKey('sponsors.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Связи с другими таблицами
    user = relationship("User", back_populates="sponsor_subscriptions", foreign_keys=[user_tg_id])
    sponsor = relationship("Sponsor", back_populates="user_subscriptions")

class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    duration_days = Column(Integer, nullable=False)  # Срок действия премиума в днях
    max_uses = Column(Integer, default=1)  # Максимальное количество использований (1 = одноразовый)
    uses_count = Column(Integer, default=0)  # Текущее количество использований
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Дата истечения самого промокода (опционально)

class PromoUse(Base):
    __tablename__ = "promo_uses"
    id = Column(Integer, primary_key=True, index=True)
    promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_at = Column(DateTime, default=datetime.datetime.utcnow)

class Achievement(Base):
    """Модель для описания достижения"""
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)  # Уникальный ключ достижения
    name = Column(String, nullable=False)  # Название достижения
    description = Column(String, nullable=False)  # Описание достижения
    icon = Column(String, default="🏆")  # Эмодзи или код иконки 
    is_purchasable = Column(Boolean, default=False)  # Можно ли купить достижение
    price = Column(Integer, default=0)  # Цена в монетах, если можно купить
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class UserAchievement(Base):
    """Модель для хранения достижений пользователя"""
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    achieved_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Отношение к моделям User и Achievement
    user = relationship("User", backref="achievements")
    achievement = relationship("Achievement")


class UserVisitedSection(Base):
    """Модель для отслеживания посещенных разделов пользователем (для достижения 'Искатель')"""
    __tablename__ = "user_visited_sections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    section = Column(String, nullable=False)  # Название раздела
    visited_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Отношение к модели User
    user = relationship("User", backref="visited_sections")

class UserSecretPurchase(Base):
    """Модель для отслеживания покупок секретного контента"""
    __tablename__ = "user_secret_purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_key = Column(String, nullable=False)  # Ключ контента
    purchased_at = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(Integer, nullable=False)  # Цена покупки
    
    # Отношение к модели User
    user = relationship("User", backref="secret_purchases")

class BotSettings(Base):
    """Модель для хранения настроек бота"""
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)  # Ключ настройки
    value = Column(String)  # Значение настройки
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


print(1)