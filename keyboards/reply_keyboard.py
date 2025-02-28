from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(locale):
    buttons = [
        [KeyboardButton(locale["button_search_team"]), KeyboardButton(locale["button_search_club"])],
        [KeyboardButton(locale["button_crystals"]), KeyboardButton(locale["button_premium"])],
        [KeyboardButton(locale["button_profile"]), KeyboardButton(locale["button_additional"])],
        [KeyboardButton(locale["button_gift"])]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
