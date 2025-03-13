import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from middleware.check_subscription import CheckSubscriptionMiddleware
from handlers.start import register_handlers_start
from handlers.menu import register_handlers_menu
from handlers.search import register_handlers_search
from handlers.announcement import register_handlers_announcement
from handlers.crystals import register_handlers_crystals
from handlers.premium import register_handlers_premium
from handlers.report import register_handlers_report
from handlers.achievements import register_handlers_achievements
from handlers.admin import register_handlers_admin
from utils.localization import get_locale

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Получаем локализацию
locale = get_locale('ru')

# Регистрация middleware
dp.middleware.setup(CheckSubscriptionMiddleware())

def register_all_handlers():
    try:
        # Регистрируем обработчики в порядке приоритета
        handlers = [
            ("admin", register_handlers_admin),  # Регистрируем первым для приоритета
            ("achievements", register_handlers_achievements),
            ("start", register_handlers_start),
            ("menu", register_handlers_menu),
            ("search", register_handlers_search),
            ("announcement", register_handlers_announcement),
            ("crystals", register_handlers_crystals),
            ("premium", register_handlers_premium),
            ("report", register_handlers_report)
        ]
        
        for name, register_func in handlers:
            try:
                logger.info(f"Registering {name} handlers...")
                if name == "admin":
                    register_func(dp)  # Админ хендлеры не требуют locale
                else:
                    register_func(dp, locale)
                logger.info(f"{name} handlers registered successfully")
            except Exception as e:
                logger.error(f"Error registering {name} handlers: {e}")
                
    except Exception as e:
        logger.error(f"Global error in register_all_handlers: {e}")

async def on_startup(_):
    try:
        register_all_handlers()
        logger.info("All handlers registered successfully")
        logger.info("Bot started!")
    except Exception as e:
        logger.error(f"Error in on_startup: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup) 