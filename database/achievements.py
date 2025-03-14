import datetime
from sqlalchemy import select, func, and_, or_
from database.models import User, Achievement, UserAchievement, UserVisitedSection, Announcement, Referral, UserSecretPurchase
from database.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

# Константы для ключей достижений
ACHIEVEMENT_MAJOR = "major"
ACHIEVEMENT_POPULAR = "popular"
ACHIEVEMENT_CLUB_FIGHTER = "club_fighter"
ACHIEVEMENT_EXPLORER = "explorer"
ACHIEVEMENT_LEGEND = "legend"
ACHIEVEMENT_LEPRECHAUN = "leprechaun"
ACHIEVEMENT_LUCKY = "lucky"
ACHIEVEMENT_FAN = "fan"
ACHIEVEMENT_BUSINESS = "business"
ACHIEVEMENT_FOLLOW_ME = "follow_me"
ACHIEVEMENT_FRIEND = "friend"

# Список необходимых разделов для достижения "Искатель"
REQUIRED_SECTIONS = [
    "search_team_menu", 
    "search_club_menu", 
    "crystals", 
    "premium", 
    "additional",
    "gift"
]

def initialize_achievements():
    """Инициализация всех достижений в базе данных, если их еще нет"""
    session = SessionLocal()
    try:
        # Проверяем есть ли уже достижения в базе
        achievements_count = session.query(Achievement).count()
        
        if achievements_count > 0:
            return
        
        # Определяем все достижения
        achievements = [
            # Покупаемое достижение
            Achievement(
                key=ACHIEVEMENT_MAJOR,
                name="Мажор",
                description="Доказательство вашей финансовой состоятельности",
                icon="💰",
                is_purchasable=True,
                price=10000
            ),
            # Создать объявление о поиске команды
            Achievement(
                key=ACHIEVEMENT_POPULAR,
                name="Популярный",
                description="Добавить объявление по поиску команды",
                icon="👥"
            ),
            # Создать объявление о поиске клуба
            Achievement(
                key=ACHIEVEMENT_CLUB_FIGHTER,
                name="Бойцовский клуб",
                description="Добавить объявление по поиску клуба",
                icon="🥊"
            ),
            # Посетить все разделы бота
            Achievement(
                key=ACHIEVEMENT_EXPLORER,
                name="Искатель",
                description="Посетить все разделы бота",
                icon="🔍"
            ),
            # Купить премиум
            Achievement(
                key=ACHIEVEMENT_LEGEND,
                name="Легенда",
                description="Купить премиум статус",
                icon="⭐"
            ),
            # Накопить 15000 монет
            Achievement(
                key=ACHIEVEMENT_LEPRECHAUN,
                name="Липрикон",
                description="Накопить 15,000 монет",
                icon="🍀"
            ),
            # Получить подарок
            Achievement(
                key=ACHIEVEMENT_LUCKY,
                name="Испытать удачу",
                description="Принять участие в розыгрыше монет",
                icon="🎁"
            ),
            # Купить секретный ролик
            Achievement(
                key=ACHIEVEMENT_FAN,
                name="Преданный фанат",
                description="Купить секретный ролик бубса",
                icon="🎬"
            ),
            # Пригласить 1 человека
            Achievement(
                key=ACHIEVEMENT_BUSINESS,
                name="Бизнес-мачо",
                description="Пригласить человека по реферальной ссылке",
                icon="💼"
            ),
            # Пригласить 10 человек
            Achievement(
                key=ACHIEVEMENT_FOLLOW_ME,
                name="Делай как я",
                description="Пригласить 10 человек по реферальной ссылке",
                icon="👑"
            ),
            # Пригласить 25 человек
            Achievement(
                key=ACHIEVEMENT_FRIEND,
                name="Настоящий друг",
                description="Пригласить 25 человек по реферальной ссылке",
                icon="❤️"
            )
        ]
        
        # Добавляем все достижения в базу
        session.add_all(achievements)
        session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации достижений: {e}")
        session.rollback()
    finally:
        session.close()

def get_all_achievements():
    """Получение всех достижений из базы данных"""
    session = SessionLocal()
    try:
        achievements = session.query(Achievement).all()
        return achievements
    finally:
        session.close()

def get_user_achievements(user_id: int):
    """Получение всех достижений пользователя"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return []
            
        # Получаем все достижения пользователя
        user_achievements = session.query(UserAchievement, Achievement).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).filter(
            UserAchievement.user_id == user.id
        ).all()
        
        # Преобразуем результат в список достижений
        achievements = []
        for ua, a in user_achievements:
            achievements.append({
                'id': a.id,
                'key': a.key,
                'name': a.name,
                'description': a.description,
                'icon': a.icon,
                'achieved_at': ua.achieved_at
            })
        
        return achievements
    finally:
        session.close()

def get_available_achievements(user_id: int):
    """Получение всех доступных достижений, которые пользователь еще не получил"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return []
            
        # Получаем ID уже полученных достижений
        earned_achievement_ids = session.query(UserAchievement.achievement_id).filter(
            UserAchievement.user_id == user.id
        ).all()
        earned_achievement_ids = [a[0] for a in earned_achievement_ids]
        
        # Получаем все достижения, которых нет в списке полученных
        available_achievements = session.query(Achievement).filter(
            ~Achievement.id.in_(earned_achievement_ids)
        ).all()
        
        return available_achievements
    finally:
        session.close()

def award_achievement(user_id: int, achievement_key: str):
    """Выдать достижение пользователю"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        # Находим достижение по ключу
        achievement = session.query(Achievement).filter(Achievement.key == achievement_key).first()
        if not achievement:
            return False
            
        # Проверяем, есть ли уже такое достижение у пользователя
        existing = session.query(UserAchievement).filter(
            UserAchievement.user_id == user.id,
            UserAchievement.achievement_id == achievement.id
        ).first()
        
        if existing:
            return False
            
        # Создаем запись о получении достижения
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id
        )
        
        session.add(user_achievement)
        session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при выдаче достижения: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def buy_achievement(user_id: int, achievement_key: str):
    """Купить достижение за монеты"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return {"success": False, "reason": "user_not_found"}
            
        # Находим достижение по ключу
        achievement = session.query(Achievement).filter(
            Achievement.key == achievement_key,
            Achievement.is_purchasable == True
        ).first()
        
        if not achievement:
            return {"success": False, "reason": "achievement_not_found"}
            
        # Проверяем, есть ли уже такое достижение у пользователя
        existing = session.query(UserAchievement).filter(
            UserAchievement.user_id == user.id,
            UserAchievement.achievement_id == achievement.id
        ).first()
        
        if existing:
            return {"success": False, "reason": "already_awarded"}
            
        # Проверяем, хватает ли монет
        if user.crystals < achievement.price:
            return {"success": False, "reason": "not_enough_coins"}
            
        # Списываем монеты и выдаем достижение
        user.crystals -= achievement.price
        
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id
        )
        
        session.add(user_achievement)
        session.commit()
        
        return {"success": True, "crystals_left": user.crystals}
    except Exception as e:
        logger.error(f"Ошибка при покупке достижения: {e}")
        session.rollback()
        return {"success": False, "reason": "error"}
    finally:
        session.close()

def record_section_visit(user_id: int, section: str):
    """Записать посещение раздела пользователем"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        # Проверяем, посещал ли пользователь этот раздел ранее
        existing = session.query(UserVisitedSection).filter(
            UserVisitedSection.user_id == user.id,
            UserVisitedSection.section == section
        ).first()
        
        if existing:
            # Раздел уже был посещен, ничего не делаем
            return False
            
        # Создаем запись о посещении
        visit = UserVisitedSection(
            user_id=user.id,
            section=section
        )
        
        session.add(visit)
        session.commit()
        
        # Проверяем, все ли необходимые разделы посещены
        visited_sections = session.query(
            UserVisitedSection.section
        ).filter(
            UserVisitedSection.user_id == user.id,
            UserVisitedSection.section.in_(REQUIRED_SECTIONS)
        ).all()
        
        visited_sections = [v[0] for v in visited_sections]
        
        # Если все разделы посещены, выдаем достижение "Искатель"
        if set(visited_sections) == set(REQUIRED_SECTIONS):
            # Находим достижение "Искатель"
            explorer_achievement = session.query(Achievement).filter(
                Achievement.key == ACHIEVEMENT_EXPLORER
            ).first()
            
            if explorer_achievement:
                # Проверяем, нет ли уже такого достижения
                existing_achievement = session.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.achievement_id == explorer_achievement.id
                ).first()
                
                if not existing_achievement:
                    # Выдаем достижение
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=explorer_achievement.id
                    )
                    
                    session.add(user_achievement)
                    session.commit()
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при записи посещения раздела: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def check_coins_achievement(user_id: int):
    """Проверить достижение 'Липрикон' (накопить 15000 монет)"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        # Проверяем баланс
        if user.crystals >= 15000:
            # Находим достижение "Липрикон"
            achievement = session.query(Achievement).filter(
                Achievement.key == ACHIEVEMENT_LEPRECHAUN
            ).first()
            
            if achievement:
                # Проверяем, нет ли уже такого достижения
                existing = session.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not existing:
                    # Выдаем достижение
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement.id
                    )
                    
                    session.add(user_achievement)
                    session.commit()
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке достижения Липрикон: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def check_referral_achievements(user_id: int):
    """Проверить реферальные достижения"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        # Считаем количество рефералов
        referral_count = session.query(func.count(Referral.id)).filter(
            Referral.referrer_id == user.tg_id
        ).scalar()
        
        awarded = False
        
        # Проверяем достижение "Бизнес-мачо" (1 реферал)
        if referral_count >= 1:
            achievement = session.query(Achievement).filter(
                Achievement.key == ACHIEVEMENT_BUSINESS
            ).first()
            
            if achievement:
                existing = session.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not existing:
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement.id
                    )
                    
                    session.add(user_achievement)
                    awarded = True
        
        # Проверяем достижение "Делай как я" (10 рефералов)
        if referral_count >= 10:
            achievement = session.query(Achievement).filter(
                Achievement.key == ACHIEVEMENT_FOLLOW_ME
            ).first()
            
            if achievement:
                existing = session.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not existing:
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement.id
                    )
                    
                    session.add(user_achievement)
                    awarded = True
        
        # Проверяем достижение "Настоящий друг" (25 рефералов)
        if referral_count >= 25:
            achievement = session.query(Achievement).filter(
                Achievement.key == ACHIEVEMENT_FRIEND
            ).first()
            
            if achievement:
                existing = session.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.achievement_id == achievement.id
                ).first()
                
                if not existing:
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement.id
                    )
                    
                    session.add(user_achievement)
                    awarded = True
        
        if awarded:
            session.commit()
            return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке реферальных достижений: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def record_secret_purchase(user_id: int, content_key: str, price: int):
    """Записать покупку секретного контента и выдать достижение"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return {"success": False, "reason": "user_not_found"}
            
        # Проверяем баланс
        if user.crystals < price:
            return {"success": False, "reason": "not_enough_coins"}
            
        # Списываем монеты
        user.crystals -= price
        
        # Записываем покупку
        purchase = UserSecretPurchase(
            user_id=user.id,
            content_key=content_key,
            price=price
        )
        
        session.add(purchase)
        
        # Выдаем достижение "Преданный фанат"
        achievement = session.query(Achievement).filter(
            Achievement.key == ACHIEVEMENT_FAN
        ).first()
        
        if achievement:
            existing = session.query(UserAchievement).filter(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement.id
            ).first()
            
            if not existing:
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
                
                session.add(user_achievement)
        
        session.commit()
        return {"success": True, "crystals_left": user.crystals}
    except Exception as e:
        logger.error(f"Ошибка при записи покупки секретного контента: {e}")
        session.rollback()
        return {"success": False, "reason": "error"}
    finally:
        session.close()

def has_purchased_secret(user_id: int, content_key: str):
    """Проверить, покупал ли пользователь секретный контент"""
    session = SessionLocal()
    try:
        # Находим внутренний ID пользователя по tg_id
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        # Проверяем наличие покупки
        purchase = session.query(UserSecretPurchase).filter(
            UserSecretPurchase.user_id == user.id,
            UserSecretPurchase.content_key == content_key
        ).first()
        
        return purchase is not None
    finally:
        session.close() 