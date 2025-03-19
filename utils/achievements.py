from typing import List, Dict
from database.models import User
from database.session import SessionLocal
from database.achievements import award_achievement, ACHIEVEMENT_LEGEND
from utils.helpers import update_user_premium

ACHIEVEMENTS = {
    "major": {
        "id": "major",
        "name": "Мажор",
        "description": "Потратить 10,000 монет",
        "emoji": "💰",
        "condition": lambda user: user.total_spent >= 10000
    },
    "popular": {
        "id": "popular",
        "name": "Популярный",
        "description": "Добавить объявление по поиску тимы",
        "emoji": "🌟",
        "condition": lambda user: user.team_announcements_count > 0
    },
    "fight_club": {
        "id": "fight_club",
        "name": "Бойцовский клуб",
        "description": "Добавить объявление по поиску клуба",
        "emoji": "🥊",
        "condition": lambda user: user.club_announcements_count > 0
    },
    "explorer": {
        "id": "explorer",
        "name": "Искатель",
        "description": "Посетить все разделы бота",
        "emoji": "🔍",
        "condition": lambda user: len(user.visited_sections or []) >= 7
    },
    "legend": {
        "id": "legend",
        "name": "Легенда",
        "description": "Купить премиум",
        "emoji": "👑",
        "condition": lambda user: user.is_premium
    },
    "leprechaun": {
        "id": "leprechaun",
        "name": "Липрикон",
        "description": "Накопить 15,000 монет",
        "emoji": "🍀",
        "condition": lambda user: user.crystals >= 15000
    },
    "lucky": {
        "id": "lucky",
        "name": "Испытать удачу",
        "description": "Принять участие в розыгрыше монет",
        "emoji": "🎲",
        "condition": lambda user: user.participated_in_giveaway
    },
    "business": {
        "id": "business",
        "name": "Бизнес-мачо",
        "description": "Пригласить человека по реферальной ссылке",
        "emoji": "💼",
        "condition": lambda user: user.referral_count >= 1
    },
    "follow_me": {
        "id": "follow_me",
        "name": "Делай как я",
        "description": "Пригласить 10 человек по реферальной ссылке",
        "emoji": "👥",
        "condition": lambda user: user.referral_count >= 10
    },
    "true_friend": {
        "id": "true_friend",
        "name": "Настоящий друг",
        "description": "Пригласить 25 человек по реферальной ссылке",
        "emoji": "🤝",
        "condition": lambda user: user.referral_count >= 25
    }
}

async def check_and_award_achievements(user_id: int) -> List[Dict]:
    """
    Проверяет и выдает достижения пользователю
    Возвращает список новых достижений
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return []

        new_achievements = []
        user_achievements = user.achievements or []

        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id not in user_achievements and achievement["condition"] and achievement["condition"](user):
                user_achievements.append(achievement_id)
                new_achievements.append(achievement)

        user.achievements = user_achievements
        db.commit()
        return new_achievements
    finally:
        db.close()

def format_achievements_message(achievements: List[str], locale: dict) -> str:
    """Форматирует сообщение со списком всех достижений с указанием полученных и неполученных"""
    total_achievements = len(ACHIEVEMENTS)
    completed_count = len(achievements) if achievements else 0
    
    message = locale.get("achievements_text", "🏆 Ваши достижения: {count}/{total}").format(
        count=completed_count,
        total=total_achievements
    ) + "\n\n"
    
    # Сначала выводим полученные достижения
    if achievements:
        message += locale.get("achievements_list", "📋 Список ваших достижений:") + "\n\n"
        for ach_id in achievements:
            if ach_id in ACHIEVEMENTS:
                achievement = ACHIEVEMENTS[ach_id]
                message += f"{achievement['emoji']} {achievement['name']} - {achievement['description']}\n"
                message += locale.get("achievement_completed", "✅ Выполнено") + "\n\n"
    else:
        message += locale.get("no_achievements", "🏅 У вас пока нет достижений. Попробуйте выполнить некоторые действия, чтобы их получить!") + "\n\n"
    
    # Затем выводим недостающие достижения
    missing_achievements = [ach for ach_id, ach in ACHIEVEMENTS.items() if ach_id not in achievements]
    if missing_achievements:
        message += locale.get("achievements_available", "📋 Доступные достижения:") + "\n\n"
        for achievement in missing_achievements:
            message += f"{achievement['emoji']} {achievement['name']} - {achievement['description']}\n"
            message += locale.get("achievement_not_completed", "❌ Не выполнено") + "\n\n"
    
    return message 

def check_premium_achievement(user_id: int):
    """Проверяет и выдает достижение 'Легенда' при покупке премиума"""
    award_achievement(user_id, ACHIEVEMENT_LEGEND) 