import json
import datetime
import logging
from datetime import timezone
from database.session import SessionLocal
from database.models import User, Announcement, Favorite, Report, Referral

logger = logging.getLogger(__name__)

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

def check_all_sponsor_subscriptions(user_id: int) -> bool:
    """
    Проверяет подписку пользователя на всех активных спонсоров
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True, если пользователь подписан на всех спонсоров, иначе False
    """
    from database.crud import get_sponsors, check_user_subscription
    
    # Получаем всех активных спонсоров
    sponsors = get_sponsors(is_active_only=True)
    
    if not sponsors:
        # Если нет активных спонсоров, считаем, что пользователь НЕ подписан
        return False
    
    # Проверяем подписку на каждого спонсора
    for sponsor in sponsors:
        if not check_user_subscription(user_id, sponsor.id):
            return False
    
    return True

def load_locale(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_user_language(user_id: int) -> str:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        language = user.language if user and user.language else 'ru'
        return load_locale('locale/' + f"{language}" + '.json')
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return load_locale('locale/ru.json')
    finally:
        session.close()


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

def get_user_announcement(user_id, announcement_type: str, get_all=False) -> dict:
    session = SessionLocal()
    query = session.query(Announcement).filter(
        Announcement.user_id == user_id,
        Announcement.announcement_type == announcement_type
    ).order_by(Announcement.created_at.desc())
    
    # Если нужно получить все объявления пользователя (не более 2-х)
    if get_all:
        announcements = query.limit(2).all()
        session.close()
        if announcements:
            return [
                {
                    "id": announcement.id,
                    "user_id": announcement.user_id,
                    "image_id": announcement.image_id,
                    "media_type": announcement.media_type,
                    "description": announcement.description,
                    "keyword": announcement.keyword,
                    "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M")
                }
                for announcement in announcements
            ]
        return []
    
    # Если нужно получить только одно объявление (для обратной совместимости)
    announcement = query.first()
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
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            user = User(
                tg_id=user_id,
                username=username,
                crystals=1000,
                created_at=datetime.datetime.now(timezone.utc)
            )
            session.add(user)
            session.commit()
            return True
        return True
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        session.rollback()
        return False
    finally:
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
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if user:
            user.language = lang
            session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating user language: {e}")
        session.rollback()
        return False
    finally:
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

async def is_user_premium(user_id: int) -> bool:
    """Проверяет, является ли пользователь премиум"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
        # Проверяем срок действия премиума
        if user.premium_until is not None and user.premium_until < datetime.datetime.now(timezone.utc):
            user.is_premium = False
            session.commit()
            return False
        return user.is_premium
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
        return False
    finally:
        session.close()


def process_premium_purchase(user_id):
    """Обрабатывает покупку премиум-статуса"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if user and user.crystals >= 500:
            user.crystals -= 500
            user.is_premium = True
            session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error processing premium purchase: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def check_user_crystals(user_id) -> int:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        return user.crystals if user else 0
    finally:
        session.close()

def get_user_crystals(user_id: int) -> int:
    """Получает количество кристаллов пользователя"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        return user.crystals if user else 0
    finally:
        session.close()

def get_user_coins(user_id: int) -> int:
    """Получает текущий баланс монет пользователя"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return 0
        return user.coins
    finally:
        session.close()

def update_user_coins(user_id: int, amount: int) -> bool:
    """Обновляет баланс монет пользователя"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
        
        # Если это вычитание монет, проверяем достаточно ли их
        if amount < 0 and user.coins + amount < 0:
            return False
            
        user.coins += amount
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating user coins: {e}")
        return False
    finally:
        session.close()

def update_user_crystals(user_id: int, amount: int):
    """Обновляет количество кристаллов пользователя"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if user:
            user.crystals += amount
            session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating user crystals: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def update_user_premium(user_id: int, expiry_date) -> bool:
    """Обновляет премиум статус пользователя"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return False
        
        user.is_premium = True
        user.premium_until = expiry_date
        user.premium_end_date = expiry_date  # Обновляем оба поля для совместимости
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при выдаче премиума: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def process_crystal_transfer(sender_id, receiver_id, amount: int):
    """Обрабатывает перевод кристаллов между пользователями"""
    session = SessionLocal()
    try:
        sender = session.query(User).filter(User.tg_id == sender_id).first()
        receiver = session.query(User).filter(User.tg_id == int(receiver_id)).first()
        
        if not sender or not receiver:
            return False, "User not found"
            
        if sender.crystals < amount:
            return False, "Insufficient crystals"
            
        sender.crystals -= amount
        receiver.crystals += amount
        session.commit()
        return True, None
    except Exception as e:
        logger.error(f"Error transferring crystals: {e}")
        session.rollback()
        return False, str(e)
    finally:
        session.close()

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
        referral = Referral(referrer_id=inviter_id, referred_id=referred_id)
        session.add(referral)
        # Начисляем пригласившему 20 монет
        user = session.query(User).filter(User.tg_id == inviter_id).first()
        if user:
            user.coins += 20
        session.commit()
    session.close()


def get_referral_count(user_id: int) -> int:
    session = SessionLocal()
    count = session.query(Referral).filter(Referral.referrer_id == user_id).count()
    session.close()
    return count

def can_receive_daily_crystals(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.tg_id == user_id).first()
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
    user = session.query(User).filter(User.tg_id == user_id).first()
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

def can_create_announcement(user_id: int, announcement_type: str) -> bool:
    """
    Проверяет, может ли пользователь создать новое объявление указанного типа.
    
    Правила:
    - Пользователи без премиума могут иметь только одно объявление любого типа
    - Премиум-пользователи могут иметь до 2-х объявлений каждого типа
    
    Args:
        user_id (int): ID пользователя
        announcement_type (str): Тип объявления ('team' или 'club')
        
    Returns:
        bool: True, если пользователь может создать новое объявление, иначе False
    """
    # Проверяем статус премиум пользователя
    has_premium = is_user_premium(user_id)
    
    # Получаем все объявления пользователя данного типа
    announcements = get_user_announcement(user_id, announcement_type, get_all=True)
    
    # Если пользователь имеет премиум, он может создать до 2-х объявлений каждого типа
    if has_premium:
        return len(announcements) < 2
    
    # Если пользователь без премиума, проверяем наличие объявлений любого типа
    team_announcements = get_user_announcement(user_id, "team", get_all=True)
    club_announcements = get_user_announcement(user_id, "club", get_all=True)
    
    # Пользователи без премиума могут иметь только одно объявление любого типа
    return len(team_announcements) + len(club_announcements) == 0

def use_promo_code(code: str, user_id: int) -> dict:
    """
    Функция-обертка для использования промокода.
    Вызывает функцию из модуля database.crud
    
    Args:
        code (str): Код промокода
        user_id (int): ID пользователя
    
    Returns:
        dict: Результат активации промокода содержащий:
            - success (bool): Успешность активации
            - error_code (str, optional): Код ошибки в случае неудачи
            - duration_days (int, optional): Срок действия премиума в днях
            - end_date (datetime, optional): Дата окончания премиума
    """
    from database.crud import use_promo_code as db_use_promo_code
    import datetime
    
    # Получаем кортежный результат из базовой функции
    success, message, duration_days = db_use_promo_code(user_id, code)
    
    # Формируем словарь с результатом
    result = {'success': success}
    
    if success:
        # Если успешно, добавляем информацию о сроке действия
        result['duration_days'] = duration_days
        # Вычисляем дату окончания премиума
        result['end_date'] = datetime.datetime.now() + datetime.timedelta(days=duration_days)
        
        # Выдаем достижение "Легенда" при активации промокода
        check_premium_achievement(user_id)
    else:
        # Если неуспешно, добавляем код ошибки на основе сообщения
        if 'не найден' in message:
            result['error_code'] = 'not_found'
        elif 'уже использовали' in message:
            result['error_code'] = 'used'
        elif 'неактивен' in message:
            result['error_code'] = 'inactive'
        elif 'истек' in message:
            result['error_code'] = 'expired'
        elif 'максимальное число раз' in message:
            result['error_code'] = 'limit_reached'
        else:
            result['error_code'] = 'unknown'
    
    return result

def record_section_visit(user_id: int, section: str):
    """Запись посещения раздела и проверка достижения 'Искатель'"""
    from database.achievements import record_section_visit as db_record_section_visit
    return db_record_section_visit(user_id, section)

def award_achievement(user_id: int, achievement_key: str):
    """Выдача достижения пользователю"""
    from database.achievements import award_achievement as db_award_achievement
    return db_award_achievement(user_id, achievement_key)

def check_announcement_achievements(user_id: int, announcement_type: str):
    """Проверяет и выдает достижения связанные с объявлениями"""
    from database.achievements import award_achievement, ACHIEVEMENT_POPULAR, ACHIEVEMENT_CLUB_FIGHTER
    
    if announcement_type == "team":
        award_achievement(user_id, ACHIEVEMENT_POPULAR)
    elif announcement_type == "club":
        award_achievement(user_id, ACHIEVEMENT_CLUB_FIGHTER)

def check_premium_achievement(user_id: int):
    """Проверяет и выдает достижение 'Легенда' при покупке премиума"""
    from database.achievements import award_achievement, ACHIEVEMENT_LEGEND
    award_achievement(user_id, ACHIEVEMENT_LEGEND)

def check_gift_achievement(user_id: int):
    """Проверяет и выдает достижение 'Испытать удачу' при получении подарка"""
    from database.achievements import award_achievement, ACHIEVEMENT_LUCKY
    award_achievement(user_id, ACHIEVEMENT_LUCKY)

def check_coins_achievement(user_id: int):
    """Проверяет и выдает достижение 'Липрикон' при накоплении 15000 монет"""
    from database.achievements import check_coins_achievement as db_check_coins_achievement
    return db_check_coins_achievement(user_id)

def check_referral_achievements(user_id: int):
    """Проверяет и выдает реферальные достижения"""
    from database.achievements import check_referral_achievements as db_check_referral_achievements
    return db_check_referral_achievements(user_id)

def display_announcement_with_keyword(announcement, locale):
    """
    Функция для форматирования отображения объявления с ключевым словом
    """
    if not announcement:
        return None
    
    # Добавляем метку Premium, если пользователь премиум
    premium_label = locale["premium_label"] + "\n" if announcement.get("is_premium") else ""
    
    # Добавляем метку ключевого слова
    keyword_label = ""
    if announcement.get("keyword"):
        keyword_text = locale.get(f"keyword_{announcement['keyword']}", announcement['keyword'])
        keyword_label = locale["keyword_label"].format(keyword=keyword_text) + "\n"
    
    # Добавляем время создания
    time_label = locale["time_label"] + " " + announcement["created_at"] + "\n"
    
    # Формируем полный текст
    return f"{premium_label}{keyword_label}{time_label}{announcement['description']}"
