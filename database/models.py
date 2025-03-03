import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()




class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, unique=True, index=True)
    username = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    crystals = Column(Integer, default=100)
    language = Column(String, default="ru")
    blocked = Column(Boolean, default=False)
    last_gift = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, nullable=False)
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

