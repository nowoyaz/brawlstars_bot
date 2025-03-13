from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.helpers import is_user_premium
from database.crud import get_premium_prices
from config import ADMIN_ID, MANAGER_LINK
from utils.helpers import get_user_language
from keyboards.inline_keyboard import premium_keyboard, premium_prices_keyboard
from database.session import SessionLocal
import datetime
from database.models import User

class PremiumStates(StatesGroup):
    waiting_for_price = State()

async def cmd_premium(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    premium_status = ""
    is_premium = is_user_premium(callback.from_user.id)
    
    if is_premium:
        # Получаем дату окончания премиума
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == callback.from_user.id).first()
            
            if user and user.premium_end_date:
                # Если дата окончания больше чем на 30 лет вперед, считаем это "навсегда"
                if user.premium_end_date > datetime.datetime.now() + datetime.timedelta(days=365*30):
                    premium_status = "\n\n" + locale["premium_active_forever"]
                else:
                    formatted_date = user.premium_end_date.strftime("%d.%m.%Y")
                    premium_status = "\n\n" + locale["premium_active_until"].format(date=formatted_date)
        finally:
            session.close()
    
    text = locale["premium_text"] + premium_status
    await callback.message.edit_text(text, reply_markup=premium_keyboard(locale, is_premium))

async def cmd_premium_prices(callback: types.CallbackQuery, locale):
    locale = get_user_language(callback.from_user.id)
    await callback.answer()
    
    # Получаем текущие цены
    prices = get_premium_prices()
    
    # Преобразуем в словарь для удобства
    prices_dict = {price.duration_type: price.price for price in prices}
    
    # Форматируем текст с ценами
    text = locale["premium_prices_text"].format(
        month=prices_dict.get("month", "500"),
        half_year=prices_dict.get("half_year", "2500"),
        year=prices_dict.get("year", "4500"),
        forever=prices_dict.get("forever", "9900")
    )
    
    await callback.message.edit_text(text, reply_markup=premium_prices_keyboard(locale))

def register_handlers_premium(dp: Dispatcher, locale):
    dp.register_callback_query_handler(lambda call: cmd_premium(call, locale), lambda c: c.data == "premium")
    dp.register_callback_query_handler(lambda call: cmd_premium_prices(call, locale), lambda c: c.data == "premium_prices")
