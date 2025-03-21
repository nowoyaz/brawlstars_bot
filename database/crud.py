import datetime
from sqlalchemy import select, update, desc, or_, func
from database.models import User, PremiumPrice, Sponsor, UserSponsorSubscription, PromoCode, PromoUse, BotSettings
from database.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

def update_user_last_gift(user_id: int) -> bool:
    """
    Обновляет время последнего подарка пользователя на текущее время
    
    Args:
        user_id (int): ID пользователя
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
            
        user.last_gift = datetime.datetime.now()
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении времени последнего подарка: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

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
                PremiumPrice(duration_days=36500, price=9900)  # навсегда
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
            price = PremiumPrice(
                duration_days=duration_days,
                price=new_price,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            session.add(price)
        
        session.commit()
        session.refresh(price)  # Обновляем объект после коммита
        return price
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()

# Функции для работы со спонсорами
def get_sponsors(is_active_only=True):
    """Получает список спонсоров"""
    session = SessionLocal()
    query = session.query(Sponsor)
    if is_active_only:
        query = query.filter(Sponsor.is_active == True)
    sponsors = query.all()
    session.close()
    return sponsors

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

def update_sponsor(sponsor_id: int, **kwargs):
    """Обновляет данные спонсора"""
    session = SessionLocal()
    try:
        sponsor = session.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
        if not sponsor:
            return False
            
        for key, value in kwargs.items():
            if value is not None:
                setattr(sponsor, key, value)
        
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

# Алиас для get_user_by_id для обратной совместимости
def get_user(user_id: int):
    """
    Алиас для функции get_user_by_id
    Получает пользователя по его Telegram ID
    """
    return get_user_by_id(user_id)

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

# ----- Функции для работы с промокодами -----

def add_promo_code(code: str, duration_days: int, max_uses: int = 1, expires_at: datetime = None):
    """
    Добавляет новый промокод
    
    Args:
        code (str): Промокод (должен быть уникальным)
        duration_days (int): Срок действия премиума в днях
        max_uses (int, optional): Максимальное количество использований. По умолчанию 1.
        expires_at (datetime, optional): Срок действия самого промокода. По умолчанию None (бессрочно).
    
    Returns:
        PromoCode: Созданный промокод или None в случае ошибки
    """
    session = SessionLocal()
    try:
        # Проверяем, что промокод уникальный
        existing = session.query(PromoCode).filter(PromoCode.code == code).first()
        if existing:
            session.close()
            return None
        
        promo = PromoCode(
            code=code,
            duration_days=duration_days,
            max_uses=max_uses,
            expires_at=expires_at,
            is_active=True
        )
        session.add(promo)
        session.commit()
        session.refresh(promo)
        result = promo
    except Exception as e:
        print(f"Error adding promo code: {e}")
        session.rollback()
        result = None
    finally:
        session.close()
    return result

def get_promo_codes(include_inactive=False):
    """
    Получает список всех промокодов
    
    Args:
        include_inactive (bool, optional): Включать ли неактивные промокоды. По умолчанию False.
    
    Returns:
        List[PromoCode]: Список промокодов
    """
    session = SessionLocal()
    query = session.query(PromoCode)
    if not include_inactive:
        query = query.filter(PromoCode.is_active == True)
    promos = query.all()
    session.close()
    return promos

def get_promo_code_by_id(promo_id: int):
    """
    Получает промокод по ID
    
    Args:
        promo_id (int): ID промокода
    
    Returns:
        PromoCode: Найденный промокод или None
    """
    session = SessionLocal()
    promo = session.query(PromoCode).filter(PromoCode.id == promo_id).first()
    session.close()
    return promo

def get_promo_code_by_code(code: str):
    """
    Получает промокод по коду
    
    Args:
        code (str): Код промокода
    
    Returns:
        PromoCode: Найденный промокод или None
    """
    session = SessionLocal()
    promo = session.query(PromoCode).filter(PromoCode.code == code).first()
    session.close()
    return promo

def delete_promo_code(promo_id: int):
    """
    Удаляет промокод по ID
    
    Args:
        promo_id (int): ID промокода
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = SessionLocal()
    try:
        promo = session.query(PromoCode).filter(PromoCode.id == promo_id).first()
        if not promo:
            session.close()
            return False
        
        session.delete(promo)
        session.commit()
        result = True
    except Exception as e:
        print(f"Error deleting promo code: {e}")
        session.rollback()
        result = False
    finally:
        session.close()
    return result

def deactivate_promo_code(promo_id: int):
    """Деактивирует промокод"""
    session = SessionLocal()
    try:
        promo = session.query(PromoCode).filter(PromoCode.id == promo_id).first()
        if not promo:
            return False
        
        promo.is_active = False
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при деактивации промокода: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def update_promo_code(promo_id: int, is_active: bool = True):
    """Обновляет статус промокода"""
    session = SessionLocal()
    try:
        promo = session.query(PromoCode).filter(PromoCode.id == promo_id).first()
        if not promo:
            return False
        
        promo.is_active = is_active
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса промокода: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def use_promo_code(user_id: int, code: str):
    """
    Использует промокод пользователем
    
    Args:
        user_id (int): Telegram ID пользователя
        code (str): Код промокода
    
    Returns:
        tuple: (success, message, duration_days)
        - success (bool): True если промокод успешно использован
        - message (str): Сообщение об успехе или ошибке
        - duration_days (int): Срок действия премиума в днях или None
    """
    session = SessionLocal()
    try:
        # Проверяем существование промокода
        promo = session.query(PromoCode).filter(PromoCode.code == code).first()
        if not promo:
            session.close()
            return False, "Промокод не найден", None
        
        # Проверяем активность промокода
        if not promo.is_active:
            session.close()
            return False, "Этот промокод уже неактивен", None
        
        # Проверяем срок действия промокода
        if promo.expires_at and promo.expires_at < datetime.datetime.now():
            session.close()
            return False, "Срок действия промокода истек", None
        
        # Проверяем количество использований
        if promo.uses_count >= promo.max_uses:
            session.close()
            return False, "Промокод уже использован максимальное число раз", None
        
        # Проверяем, не использовал ли пользователь уже этот промокод
        existing_use = session.query(PromoUse).filter(
            PromoUse.promo_id == promo.id,
            PromoUse.user_tg_id == user_id
        ).first()
        if existing_use:
            session.close()
            return False, "Вы уже использовали этот промокод", None
        
        # Используем промокод
        promo_use = PromoUse(promo_id=promo.id, user_tg_id=user_id)
        session.add(promo_use)
        
        # Увеличиваем счетчик использований
        promo.uses_count += 1
        
        # Если достигнуто максимальное количество использований, деактивируем промокод
        if promo.uses_count >= promo.max_uses:
            promo.is_active = False
        
        # Применяем премиум-статус пользователю
        user = session.query(User).filter(User.tg_id == user_id).first()
        if not user:
            session.rollback()
            session.close()
            return False, "Пользователь не найден", None
        
        # Определяем дату окончания премиума
        now = datetime.datetime.now()
        if not user.is_premium:
            # Если у пользователя нет премиума, устанавливаем новую дату
            user.is_premium = True
            user.premium_end_date = now + datetime.timedelta(days=promo.duration_days)
            # Синхронизируем поле premium_until с premium_end_date
            user.premium_until = user.premium_end_date
        else:
            # Если у пользователя уже есть премиум, продлеваем его
            if user.premium_end_date and user.premium_end_date > now:
                user.premium_end_date = user.premium_end_date + datetime.timedelta(days=promo.duration_days)
            else:
                user.premium_end_date = now + datetime.timedelta(days=promo.duration_days)
            # Синхронизируем поле premium_until с premium_end_date
            user.premium_until = user.premium_end_date
        
        session.commit()
        return True, "Промокод успешно активирован", promo.duration_days
    except Exception as e:
        print(f"Error using promo code: {e}")
        session.rollback()
        return False, f"Произошла ошибка при активации промокода", None
    finally:
        session.close()

# ----- Конец функций для работы с промокодами ----- 

def create_new_user(tg_id: int, username: str = None, first_name: str = None, referrer_id: int = None):
    """
    Создает нового пользователя в базе данных
    
    Args:
        tg_id (int): Telegram ID пользователя
        username (str): Имя пользователя в Telegram (опционально)
        first_name (str): Имя пользователя (опционально)
        referrer_id (int): ID пользователя, который пригласил нового пользователя (опционально)
    
    Returns:
        User: Созданный пользователь
    """
    session = SessionLocal()
    try:
        # Проверяем, существует ли пользователь
        user = session.query(User).filter(User.tg_id == tg_id).first()
        if user:
            return user
            
        # Создаем нового пользователя
        user = User(
            tg_id=tg_id,
            username=username,
            first_name=first_name,
            crystals=100,  # Начальное количество кристаллов
            created_at=datetime.datetime.now()
        )
        session.add(user)
        session.commit()
        
        # Если указан ID реферера, обрабатываем реферальную систему
        if referrer_id:
            from utils.helpers import process_referral
            process_referral(tg_id, referrer_id)
            
        return user
    except Exception as e:
        session.rollback()
        print(f"Error creating new user: {e}")
        return None
    finally:
        session.close()

def get_user_by_tg_id(tg_id: int):
    """
    Получает пользователя по его Telegram ID
    
    Args:
        tg_id (int): Telegram ID пользователя
    
    Returns:
        User: Пользователь или None, если не найден
    """
    session = SessionLocal()
    try:
        return session.query(User).filter(User.tg_id == tg_id).first()
    finally:
        session.close()

def is_user_banned(tg_id: int) -> bool:
    """
    Проверяет, заблокирован ли пользователь
    
    Args:
        tg_id (int): Telegram ID пользователя
    
    Returns:
        bool: True, если пользователь заблокирован, False в противном случае
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        return user.blocked if user else False
    finally:
        session.close()

def add_user_crystals(tg_id: int, amount: int) -> bool:
    """
    Добавляет кристаллы пользователю
    
    Args:
        tg_id (int): Telegram ID пользователя
        amount (int): Количество кристаллов для добавления
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            return False
            
        user.crystals += amount
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding crystals to user: {e}")
        return False
    finally:
        session.close()

def update_user_crystals(tg_id: int, amount: int) -> bool:
    """
    Устанавливает определенное количество кристаллов пользователю
    
    Args:
        tg_id (int): Telegram ID пользователя
        amount (int): Новое количество кристаллов
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            return False
            
        user.crystals = amount
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating user crystals: {e}")
        return False
    finally:
        session.close()

def update_user_coins(tg_id: int, amount: int) -> bool:
    """
    Устанавливает определенное количество монет пользователю
    
    Args:
        tg_id (int): Telegram ID пользователя
        amount (int): Новое количество монет
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            return False
            
        user.coins = amount
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating user coins: {e}")
        return False
    finally:
        session.close()

def get_bot_setting(key: str) -> str:
    """Получить значение настройки бота"""
    session = SessionLocal()
    try:
        setting = session.query(BotSettings).filter(BotSettings.key == key).first()
        return setting.value if setting else None
    finally:
        session.close()

def set_bot_setting(key: str, value: str) -> bool:
    """Установить значение настройки бота"""
    session = SessionLocal()
    try:
        setting = session.query(BotSettings).filter(BotSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = BotSettings(key=key, value=value)
            session.add(setting)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error setting bot setting: {e}")
        session.rollback()
        return False
    finally:
        session.close() 