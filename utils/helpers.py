import json
import datetime
from database.session import SessionLocal
from database.models import User, Announcement, Favorite, Report

def load_locale(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_next_announcement(announcement_type: str, current_user_id: int) -> dict:
    session = SessionLocal()
    # Для простоты фильтруем только по типу и исключаем свои объявления
    announcement = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id
    ).order_by(Announcement.created_at.desc()).first()
    session.close()
    if announcement:
        return {
            "id": announcement.id,
            "user_id": announcement.user_id,
            "image_id": announcement.image_id,
            "description": announcement.description,
            "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M")
        }
    return None

def get_announcements_count(announcement_type: str, current_user_id: int) -> int:
    session = SessionLocal()
    count = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id
    ).count()
    session.close()
    return count

def save_announcement(user_id, announcement_type, image_id, description):
    session = SessionLocal()
    announcement = Announcement(
        user_id=user_id,
        announcement_type=announcement_type,
        image_id=image_id,
        description=description,
        created_at=datetime.datetime.utcnow()
    )
    session.add(announcement)
    session.commit()
    session.close()

def get_user_announcement(user_id, announcement_type: str) -> dict:
    session = SessionLocal()
    announcement = session.query(Announcement).filter(
        Announcement.user_id == user_id,
        Announcement.announcement_type == announcement_type
    ).order_by(Announcement.created_at.desc()).first()
    session.close()
    if announcement:
        return {
            "id": announcement.id,
            "user_id": announcement.user_id,
            "image_id": announcement.image_id,
            "description": announcement.description,
            "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M")
        }
    return None

def report_announcement(user_id: int, announcement_id: int):
    session = SessionLocal()
    existing_report = session.query(Report).filter_by(reporter_id=user_id, announcement_id=announcement_id).first()
    if not existing_report:
        report = Report(reporter_id=user_id, announcement_id=announcement_id, created_at=datetime.datetime.utcnow())
        session.add(report)
        session.commit()
    session.close()

def add_favorite(user_id: int, announcement_id: int):
    session = SessionLocal()
    existing_favorite = session.query(Favorite).filter_by(user_id=user_id, announcement_id=announcement_id).first()
    if not existing_favorite:
        favorite = Favorite(user_id=user_id, announcement_id=announcement_id)
        session.add(favorite)
        session.commit()
    session.close()


def process_premium_purchase(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if user and user.crystals >= 500:
        user.crystals -= 500
        user.is_premium = True
        session.commit()
    session.close()


def check_user_crystals(user_id) -> int:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user.crystals if user else 0

def get_user_crystals(user_id) -> int:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user.crystals if user else 0


def process_crystal_transfer(sender_id, receiver_id, amount: int):
    session = SessionLocal()
    sender = session.query(User).filter(User.id == sender_id).first()
    receiver = session.query(User).filter(User.id == int(receiver_id)).first()
    if not receiver:
        session.close()
        return False, "❌ Адрес не найден"
    if sender.crystals < amount:
        session.close()
        return False, "❌ Недостаточно кристаллов"
    sender.crystals -= amount
    receiver.crystals += amount
    session.commit()
    session.close()
    return True, "✅ Перевод успешно выполнен"