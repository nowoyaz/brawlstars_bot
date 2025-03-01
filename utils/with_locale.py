import json
import datetime
from database.session import SessionLocal
from database.models import User, Announcement, Favorite, Report, Referral

def load_locale(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_user_language(user_id: int) -> str:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user.language if user and user.language else "ru"


def get_next_announcement(announcement_type: str, current_user_id: int) -> dict:
    session = SessionLocal()
    # Получаем список id пользователей, чьи объявления уже репортнул текущий пользователь
    reported_user_ids = session.query(Announcement.user_id)\
        .join(Report, Report.announcement_id == Announcement.id)\
        .filter(Report.reporter_id == current_user_id).distinct().all()
    reported_user_ids = [uid for (uid,) in reported_user_ids]
    announcement = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id,
        ~Announcement.user_id.in_(reported_user_ids)
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
    reported_user_ids = session.query(Announcement.user_id)\
        .join(Report, Report.announcement_id == Announcement.id)\
        .filter(Report.reporter_id == current_user_id).distinct().all()
    reported_user_ids = [uid for (uid,) in reported_user_ids]
    count = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id,
        ~Announcement.user_id.in_(reported_user_ids)
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


def report_announcement(user_id: int, announcement_id: int, reason: str):
    session = SessionLocal()
    existing_report = session.query(Report).filter_by(reporter_id=user_id, announcement_id=announcement_id).first()
    if not existing_report:
        report = Report(
            reporter_id=user_id,
            announcement_id=announcement_id,
            reason=reason,  # Передаём выбранную причину
            created_at=datetime.datetime.utcnow()
        )
        session.add(report)
        session.commit()
    session.close()

def ensure_user_exists(user_id, username):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=username, crystals=1000, created_at=datetime.datetime.utcnow())
        session.add(user)
        session.commit()
    session.close()


def get_favorites_list(user_id: int) -> list:
    session = SessionLocal()
    # Предполагается, что у вас есть таблица Favorite с полями user_id и announcement_id
    favorites = session.query(Favorite).filter(Favorite.user_id == user_id).all()
    session.close()
    return [fav.announcement_id for fav in favorites]

def remove_favorite(user_id: int, announcement_id: int):
    session = SessionLocal()
    favorite = session.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.announcement_id == announcement_id
    ).first()
    if favorite:
        session.delete(favorite)
        session.commit()
    session.close()

def update_user_language(user_id: int, lang: str):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.language = lang
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

def get_announcement_by_id(announcement_id: int) -> dict:
    session = SessionLocal()
    announcement = session.query(Announcement).filter(Announcement.id == announcement_id).first()
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

def is_user_premium(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user.is_premium if user else False



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

def get_announcements_list(announcement_type: str, current_user_id: int) -> list:
    session = SessionLocal()
    # Получаем список ID пользователей, чьи объявления уже репортнул текущий пользователь
    reported_user_ids = session.query(Announcement.user_id)\
        .join(Report, Report.announcement_id == Announcement.id)\
        .filter(Report.reporter_id == current_user_id).distinct().all()
    reported_user_ids = [uid for (uid,) in reported_user_ids]
    announcements = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id,
        ~Announcement.user_id.in_(reported_user_ids)
    ).order_by(Announcement.created_at.desc()).all()
    session.close()
    return [ann.id for ann in announcements]

def get_filtered_announcement(announcement_type: str, current_user_id: int, order: str = "new") -> list:
    session = SessionLocal()
    # Исключаем объявления от пользователей, которых уже репортнул текущий пользователь
    reported_user_ids = session.query(Announcement.user_id)\
        .join(Report, Report.announcement_id == Announcement.id)\
        .filter(Report.reporter_id == current_user_id).distinct().all()
    reported_user_ids = [uid for (uid,) in reported_user_ids]
    query = session.query(Announcement).filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id,
        ~Announcement.user_id.in_(reported_user_ids)
    )
    if order == "new":
        query = query.order_by(Announcement.created_at.desc())
    elif order == "old":
        query = query.order_by(Announcement.created_at.asc())
    elif order == "premium":
        # При выборе премиум-фильтра показываем только объявления от премиум пользователей
        from database.models import User
        query = query.join(User, Announcement.user_id == User.id)\
                     .filter(User.is_premium == True)\
                     .order_by(Announcement.created_at.desc())
    announcements = query.all()
    session.close()
    return [ann.id for ann in announcements]


def get_announcement_by_id(announcement_id: int) -> dict:
    session = SessionLocal()
    announcement = session.query(Announcement).filter(Announcement.id == announcement_id).first()
    session.close()
    if announcement:
        from utils.helpers import is_user_premium
        return {
            "id": announcement.id,
            "user_id": announcement.user_id,
            "image_id": announcement.image_id,
            "description": announcement.description,
            "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_premium": is_user_premium(announcement.user_id)
        }
    return None


def get_user_announcements_count(user_id: int, announcement_type: str) -> int:
    session = SessionLocal()
    count = session.query(Announcement).filter(
        Announcement.user_id == user_id,
        Announcement.announcement_type == announcement_type
    ).count()
    session.close()
    return count


def process_referral(referred_id: int, inviter_id: int):
    session = SessionLocal()
    # Проверяем, не был ли уже зафиксирован реферал
    existing = session.query(Referral).filter(Referral.referred_id == referred_id).first()
    if not existing and referred_id != inviter_id:
        referral = Referral(inviter_id=inviter_id, referred_id=referred_id)
        session.add(referral)
        # Начисляем пригласившему 20 кристаллов
        user = session.query(User).filter(User.id == inviter_id).first()
        if user:
            user.crystals += 20
        session.commit()
    session.close()


def get_referral_count(user_id: int) -> int:
    session = SessionLocal()
    count = session.query(Referral).filter(Referral.inviter_id == user_id).count()
    session.close()
    return count