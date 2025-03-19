TOKEN = "7517432356:AAE-pIF4xczh8tZp7_phZ66f6XKG8zWBMbQ"
ADMIN_ID = 7139312538  # ID админа
CHANNEL_LINK = "https://t.me/bubser_bs"  # Ссылка на канал
CHANNEL_ID = -1001217099447  # ID канала (числовой формат)
SUPPORT_LINK = "https://t.me/bubserbot_support"
MANAGER_LINK = "https://t.me/bubserbot_support"  # Ссылка на менеджера для покупки премиума
ADMIN_IDS = [7139312538, 948864328, 7634690662]  # Список ID администраторов

# Для Dokku PostgreSQL URL будет автоматически добавлен в переменную окружения DATABASE_URL
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/brawlstars_bot")