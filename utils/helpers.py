import json
import datetime
from database.session import SessionLocal
from database.models import User, Announcement, Favorite, Report

def load_locale(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

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
    """
    Возвращает список ID объявлений для заданной категории, отсортированных по порядку:
      - "new": от новых к старым
      - "old": от старых к новым
      - "premium": сначала объявления от премиум-пользователей, потом обычные, каждый порядок по дате (от новых к старым)
    Исключает объявления текущего пользователя и объявления от пользователей, которых он репортил.
    """
    session = SessionLocal()
    # Получаем список id пользователей, чьи объявления уже репортировал текущий пользователь
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
        # Предполагаем, что таблица User содержит флаг is_premium
        from database.models import User
        query = query.join(User, Announcement.user_id == User.id).order_by(User.is_premium.desc(), Announcement.created_at.desc())
    announcements = query.all()
    session.close()
    return [ann.id for ann in announcements]

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
