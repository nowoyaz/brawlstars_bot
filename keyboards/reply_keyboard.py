from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(locale):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton(locale["button_search_team"]), KeyboardButton(locale["button_search_club"])
    )
    kb.add(
        KeyboardButton(locale["button_crystals"]), KeyboardButton(locale["button_premium"])
    )
    kb.add(
        KeyboardButton(locale["button_additional"])
    )
    kb.add(
        KeyboardButton(locale["button_gift"])
    )
    return kb
