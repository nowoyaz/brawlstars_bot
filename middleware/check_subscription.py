from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from config import CHANNEL_ID, CHANNEL_LINK
from keyboards.inline_keyboard import start_keyboard
import logging

logger = logging.getLogger(__name__)

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if not update.message and not update.callback_query:
            return
            
        # Получаем пользователя
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        
        # Пропускаем команду /start и проверку подписки
        if update.message and update.message.text == "/start":
            return
            
        if update.callback_query and update.callback_query.data == "check_subscription":
            return
        
        # Проверяем подписку
        is_subscribed = await self.is_subscribed(user_id)
        if not is_subscribed:
            # Получаем объекты для отправки сообщения
            locale = data.get("locale", None)
            if update.message:
                await self.send_subscription_message(update.message, None, locale)
            elif update.callback_query:
                await self.send_subscription_message(None, update.callback_query, locale)
                
            raise CancelHandler()
    
    async def is_subscribed(self, user_id):
        try:
            # Проверяем статус подписки
            bot = self._dp.bot
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            # Проверяем, что пользователь не покинул канал
            return member.status not in ["left", "kicked", "banned"]
        except Exception as e:
            logger.error(f"Ошибка при проверке подписки: {e}")
            return False
    
    async def send_subscription_message(self, message, callback_query, locale):
        if not locale:
            text = f"❗️ Для использования бота необходима подписка на канал.\n\nПодпишитесь на канал {CHANNEL_LINK} и нажмите кнопку «Проверить подписку»"
        else:
            text = locale.get("subscription_required", "").format(channel_link=CHANNEL_LINK)
            
        keyboard = start_keyboard(locale if locale else {
            "button_start": "✅ Проверить подписку",
            "button_channel": "📣 Перейти на канал"
        })
        
        if callback_query:
            await callback_query.message.edit_text(text=text, reply_markup=keyboard)
        else:
            await message.answer(text=text, reply_markup=keyboard)