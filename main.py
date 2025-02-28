import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN
from utils.helpers import load_locale
from middleware.delay_middleware import DelayMiddleware
from middleware.premium_middleware import PremiumMiddleware
from middleware.ban_middleware import BanMiddleware

from database.session import init_db

# Импортируем обработчики
from handlers import start, menu, search, report, premium, crystals, announcement

logging.basicConfig(level=logging.INFO)

LOCALE = load_locale("locale/ru.json")
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(DelayMiddleware())
dp.middleware.setup(PremiumMiddleware())
dp.middleware.setup(BanMiddleware())

start.register_handlers_start(dp, LOCALE)
menu.register_handlers_menu(dp, LOCALE)
search.register_handlers_search(dp, LOCALE)
report.register_handlers_report(dp, LOCALE)
premium.register_handlers_premium(dp, LOCALE)
crystals.register_handlers_crystals(dp, LOCALE)
announcement.register_announcement_handlers(dp, LOCALE)

async def on_startup(dp):
    init_db()
    logging.info("Бот запущен!")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
