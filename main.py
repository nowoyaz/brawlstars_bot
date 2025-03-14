import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN
from utils.helpers import load_locale
from middleware.delay_middleware import DelayMiddleware
from middleware.premium_middleware import PremiumMiddleware
from middleware.ban_middleware import BanMiddleware

from database.session import init_db
from utils.helpers import load_locale
# Импортируем обработчики
from handlers import start, menu, search, report, premium, crystals, announcement, gift, additional, favorites, language, admin
logging.basicConfig(level=logging.INFO)

LOCALE = load_locale("locale/ru.json")
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(BanMiddleware())
dp.middleware.setup(DelayMiddleware())
dp.middleware.setup(PremiumMiddleware())


start.register_handlers_start(dp, LOCALE)
menu.register_handlers_menu(dp, LOCALE)
search.register_handlers_search(dp, LOCALE)
report.register_handlers_report(dp, LOCALE)
premium.register_handlers_premium(dp, LOCALE)
crystals.register_handlers_crystals(dp, LOCALE)
announcement.register_announcement_handlers(dp, LOCALE)
gift.register_handlers_gift(dp, LOCALE)
additional.register_handlers_additional(dp, LOCALE)
favorites.register_handlers_favorites(dp, LOCALE)
language.register_handlers_language(dp, LOCALE)
admin.register_handlers_admin(dp, LOCALE)

async def on_startup(dp):
    init_db()
    logging.info("Бот запущен!")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
