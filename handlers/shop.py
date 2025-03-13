import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from database.session import SessionLocal
from database.models import User
from keyboards.inline_keyboard import shop_keyboard, additional_keyboard
from utils.achievements import check_and_award_achievements

SECRET_VIDEO_PRICE = 1000  # Цена видео в монетах
SECRET_VIDEO_URL = "https://example.com/secret_video"  # Замените на реальную ссылку

async def show_shop(callback: types.CallbackQuery, locale):
    """Показывает магазин"""
    await callback.answer()
    text = locale["shop_text"].format(video_price=SECRET_VIDEO_PRICE)
    await callback.message.edit_text(text, reply_markup=shop_keyboard(locale))

async def buy_secret_video(callback: types.CallbackQuery, locale):
    """Обработка покупки секретного видео"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()
        if not user:
            await callback.answer(locale["user_not_found"], show_alert=True)
            return

        if user.crystals < SECRET_VIDEO_PRICE:
            await callback.answer(
                locale["insufficient_crystals"].format(balance=user.crystals, price=SECRET_VIDEO_PRICE),
                show_alert=True
            )
            return

        # Списываем монеты
        user.crystals -= SECRET_VIDEO_PRICE
        db.commit()

        # Проверяем достижение
        new_achievements = await check_and_award_achievements(user.user_id)
        
        # Отправляем ссылку на видео в личку
        await callback.bot.send_message(
            callback.from_user.id,
            locale["video_purchased"].format(url=SECRET_VIDEO_URL)
        )

        # Уведомляем о покупке
        await callback.answer(locale["purchase_success"], show_alert=True)

        # Если получено достижение, показываем уведомление
        if new_achievements:
            for achievement in new_achievements:
                await callback.bot.send_message(
                    callback.from_user.id,
                    locale["new_achievement"].format(
                        emoji=achievement["emoji"],
                        name=achievement["name"],
                        description=achievement["description"]
                    )
                )

        # Обновляем сообщение с магазином
        await callback.message.edit_text(
            locale["shop_text"].format(video_price=SECRET_VIDEO_PRICE),
            reply_markup=shop_keyboard(locale)
        )

    except Exception as e:
        logging.error(f"Error in buy_secret_video: {e}")
        await callback.answer(locale["purchase_error"], show_alert=True)
    finally:
        db.close()

async def back_to_additional(callback: types.CallbackQuery, locale):
    """Возврат в дополнительное меню"""
    await callback.answer()
    await callback.message.edit_text(
        locale["additional_text"],
        reply_markup=additional_keyboard(locale)
    )

def register_handlers_shop(dp: Dispatcher, locale):
    """Регистрация обработчиков магазина"""
    dp.register_callback_query_handler(
        lambda c: show_shop(c, locale),
        lambda c: c.data == "shop"
    )
    dp.register_callback_query_handler(
        lambda c: buy_secret_video(c, locale),
        lambda c: c.data == "buy_secret_video"
    )
    dp.register_callback_query_handler(
        lambda c: back_to_additional(c, locale),
        lambda c: c.data == "back_to_additional"
    ) 