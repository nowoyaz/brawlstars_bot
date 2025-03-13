import json
import datetime
from datetime import timezone
from database.session import SessionLocal
from database.models import User, Announcement, Favorite, Report, Referral

async def check_channel_subscription(bot, user_id: int, channel_id: str) -> bool:
    """
    Проверяет, подписан ли пользователь на канал
    
    Args:
        bot: Объект бота
        user_id: ID пользователя
        channel_id: ID канала или юзернейм канала
    
    Returns:
        bool: True, если пользователь подписан, иначе False
    """
    try:
        # Попытка получить информацию о подписке пользователя
        member = await bot.get_chat_member(channel_id, user_id)
        # Проверяем, что пользователь не исключен из канала (left, kicked, banned)
        return member.status not in ['left', 'kicked', 'banned']
    except Exception as e:
        print(f"Ошибка при проверке подписки: {str(e)}")
        return False  # В случае ошибки считаем, что пользователь не подписан

def load_locale(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_user_language(user_id: int) -> str:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return load_locale('locale/' + f"{user.language if user and user.language else 'ru'}"+'.json')


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
    
    user = None
    if announcement:
        user = session.query(User).filter(User.id == announcement.user_id).first()
    
    session.close()
    if announcement:
        return {
            "id": announcement.id,
            "user_id": announcement.user_id,
            "image_id": announcement.image_id,
            "media_type": announcement.media_type,
            "description": announcement.description,
            "keyword": announcement.keyword,
            "is_premium": user.is_premium if user else False,
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

def save_announcement(user_id: int, announcement_type: str, image_id: str, description: str, keyword: str = None, media_type: str = "photo"):
    session = SessionLocal()
    announcement = Announcement(
        user_id=user_id,
        announcement_type=announcement_type,
        image_id=image_id,
        media_type=media_type,
        description=description,
        keyword=keyword,
        created_at=datetime.datetime.now(timezone.utc)
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
            "media_type": announcement.media_type,
            "description": announcement.description,
            "keyword": announcement.keyword,
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
            reason=reason,
            created_at=datetime.datetime.now(timezone.utc)
        )
        session.add(report)
        session.commit()
    session.close()

def ensure_user_exists(user_id, username):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, tg_id=user_id, username=username, crystals=1000, created_at=datetime.datetime.now(timezone.utc))
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
        from utils.helpers import is_user_premium
        return {
            "id": announcement.id,
            "user_id": announcement.user_id,
            "image_id": announcement.image_id,
            "media_type": announcement.media_type,
            "description": announcement.description,
            "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_premium": is_user_premium(announcement.user_id),
            "announcement_type": announcement.announcement_type,
            "keyword": announcement.keyword
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
        return False, "❌ Недостаточно монет"
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
    
    # Сначала получаем премиум-объявления
    premium_announcements = session.query(Announcement.id)\
        .join(User, User.id == Announcement.user_id)\
        .filter(
            Announcement.announcement_type == announcement_type,
            Announcement.user_id != current_user_id,
            ~Announcement.user_id.in_(reported_user_ids),
            User.is_premium == True
        ).order_by(Announcement.created_at.desc()).all()
    
    # Затем получаем обычные объявления
    regular_announcements = session.query(Announcement.id)\
        .join(User, User.id == Announcement.user_id)\
        .filter(
            Announcement.announcement_type == announcement_type,
            Announcement.user_id != current_user_id,
            ~Announcement.user_id.in_(reported_user_ids),
            User.is_premium == False
        ).order_by(Announcement.created_at.desc()).all()
    
    # Объединяем результаты: сначала премиум, потом обычные
    announcements = [ann_id for (ann_id,) in premium_announcements] + [ann_id for (ann_id,) in regular_announcements]
    
    session.close()
    return announcements

def get_paginated_announcements(announcement_type: str, current_user_id: int, page: int = 0) -> dict:
    """
    Получает объявления с поддержкой пагинации.
    Возвращает словарь с текущим объявлением, общим количеством и флагами наличия следующей/предыдущей страницы.
    """
    announcement_list = get_announcements_list(announcement_type, current_user_id)
    total_count = len(announcement_list)
    
    result = {
        "total_count": total_count,
        "current_page": page,
        "has_next": False,
        "has_prev": False,
        "current_announcement": None
    }
    
    if total_count == 0:
        return result
    
    # Проверяем границы page
    if page < 0:
        page = 0
    elif page >= total_count:
        page = total_count - 1
    
    result["current_page"] = page
    result["has_next"] = page < total_count - 1
    result["has_prev"] = page > 0
    
    current_id = announcement_list[page]
    result["current_announcement"] = get_announcement_by_id(current_id)
    
    return result

def get_filtered_announcement(announcement_type: str, current_user_id: int, order: str = "new", keyword: str = None) -> list:
    session = SessionLocal()
    # Отладочная информация
    print(f"GET FILTERED: type={announcement_type}, order={order}, keyword={keyword}")
    
    # Получаем список id пользователей, чьи объявления уже репортнул текущий пользователь
    reported_user_ids = session.query(Announcement.user_id)\
        .join(Report, Report.announcement_id == Announcement.id)\
        .filter(Report.reporter_id == current_user_id).distinct().all()
    reported_user_ids = [uid for (uid,) in reported_user_ids]
    
    # Показываем все доступные ключевые слова в базе (для отладки)
    all_keywords = session.query(Announcement.keyword, Announcement.id).filter(
        Announcement.announcement_type == announcement_type
    ).all()
    print(f"All keywords in DB for type {announcement_type}: {[(k[0], k[1]) for k in all_keywords]}")
    
    # Джойним с таблицей пользователей для доступа к полю is_premium
    base_query = session.query(Announcement.id).join(User, User.id == Announcement.user_id)
    
    # Базовые фильтры, применяемые всегда
    base_query = base_query.filter(
        Announcement.announcement_type == announcement_type,
        Announcement.user_id != current_user_id,
        ~Announcement.user_id.in_(reported_user_ids)
    )
    
    # Фильтр по ключевому слову
    if keyword and keyword != "all":
        base_query = base_query.filter(Announcement.keyword == keyword)
    
    # Применяем сортировку в зависимости от order
    if order == "new":
        base_query = base_query.order_by(Announcement.created_at.desc())
    elif order == "old":
        base_query = base_query.order_by(Announcement.created_at.asc())
    elif order == "premium":
        base_query = base_query.filter(User.is_premium == True)\
                              .order_by(Announcement.created_at.desc())
    
    # Получаем результаты
    announcements = base_query.all()
    
    # Отладочная информация
    print(f"Found {len(announcements)} announcements")
    
    session.close()
    
    # Преобразуем результат в список id
    return [ann_id for (ann_id,) in announcements]


def get_user_announcements_count(user_id: int, announcement_type: str = None) -> int:
    session = SessionLocal()
    
    # Если тип не указан, считаем все объявления пользователя
    if announcement_type is None:
        count = session.query(Announcement).filter(
            Announcement.user_id == user_id
        ).count()
    else:
        # Если тип указан, считаем только объявления указанного типа
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
        # Начисляем пригласившему 20 монет
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

def can_receive_daily_crystals(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return False
    
    now = datetime.datetime.now(timezone.utc)
    if user.last_gift is None:
        session.close()
        return True
    
    # Проверяем, прошло ли время с последнего получения (проверяем по дате)
    last_gift_date = user.last_gift.date()
    current_date = now.date()
    
    session.close()
    return current_date > last_gift_date

def give_daily_crystals(user_id: int) -> tuple[bool, int]:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return False, 0
    
    if not can_receive_daily_crystals(user_id):
        session.close()
        return False, 0
    
    # Даем 100 кристаллов
    crystals_amount = 100
    user.crystals += crystals_amount
    user.last_gift = datetime.datetime.now(timezone.utc)
    session.commit()
    session.close()
    return True, crystals_amount