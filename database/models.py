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

class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    reward = Column(Integer, nullable=False, default=0)  # Награда в монетах, оставляем для совместимости
    channel_id = Column(String, nullable=True)  # ID канала для проверки подписки
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

