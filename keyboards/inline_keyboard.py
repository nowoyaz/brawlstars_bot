from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK

def start_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_start"], callback_data="menu"),
        InlineKeyboardButton(text=locale["button_channel"], url=CHANNEL_LINK)
    )
    return kb

def inline_main_menu_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_search_team"], callback_data="search_team_menu"),
        InlineKeyboardButton(text=locale["button_search_club"], callback_data="search_club_menu")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_crystals"], callback_data="crystals"),
        InlineKeyboardButton(text=locale["button_premium"], callback_data="premium")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_profile"], callback_data="profile"),
        InlineKeyboardButton(text=locale["button_additional"], callback_data="additional")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_gift"], callback_data="gift")
    )
    return kb

# Клавиатуры для поиска команды
def search_team_menu_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["button_search"], callback_data="search_team_search"),
        InlineKeyboardButton(text=locale["button_my_announcement"], callback_data="my_announcement_team"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    return kb

def search_options_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["button_normal_search"], callback_data="normal_search_team"),
        InlineKeyboardButton(text=locale["button_filtered_search"], callback_data="filtered_search_team"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu")
    )
    return kb

# Клавиатуры для поиска клуба
def search_club_menu_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["button_search"], callback_data="search_club_search"),
        InlineKeyboardButton(text=locale["button_my_announcement"], callback_data="my_announcement_club"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    return kb

def search_options_club_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["button_normal_search"], callback_data="normal_search_club"),
        InlineKeyboardButton(text=locale["button_filtered_search"], callback_data="filtered_search_club"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu")
    )
    return kb

# Клавиатура подтверждения для обычного поиска
def confirmation_keyboard(locale, suffix="team"):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_okay"], callback_data=f"confirm_normal_search_{suffix}"))
    return kb

# Клавиатура для отображения найденного объявления
def announcement_keyboard(locale, announcement_id, user_id, has_next, announcement_type):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_write"], url=f"tg://user?id={user_id}"),
        InlineKeyboardButton(text=locale["button_report"], callback_data=f"report:{announcement_id}:{announcement_type}")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_favorite"], callback_data=f"favorite:{announcement_id}:{announcement_type}")
    )
    if has_next:
        kb.add(InlineKeyboardButton(text=locale["button_next"], callback_data=f"next:{announcement_type}"))
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
    return kb

# Клавиатура для просмотра объявления пользователя
def announcement_view_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
    # Если требуется разделение по типу, можно изменить callback_data ниже
    kb.add(InlineKeyboardButton(text=locale["button_create_new"], callback_data="create_new_team"))
    return kb

# Клавиатура для репортов
def report_reason_keyboard(locale, announcement_id, announcement_type):
    kb = InlineKeyboardMarkup(row_width=2)
    reasons = [
        (locale["report_reason_ad"], "ad"),
        (locale["report_reason_links"], "links"),
        (locale["report_reason_bad_language"], "bad_language"),
        (locale["report_reason_18+"], "18+"),
        (locale["report_reason_other"], "other")
    ]
    for text, reason in reasons:
        kb.insert(InlineKeyboardButton(text=text, callback_data=f"report_reason:{announcement_id}:{reason}:{announcement_type}"))
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu"))
    return kb

# Клавиатура для фильтров поиска
def search_filters_keyboard(locale, announcement_type):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["filter_new"], callback_data=f"filtered_search_{announcement_type}_new"),
        InlineKeyboardButton(text=locale["filter_old"], callback_data=f"filtered_search_{announcement_type}_old"),
        InlineKeyboardButton(text=locale["filter_premium"], callback_data=f"filtered_search_{announcement_type}_premium"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu")
    )
    return kb

def report_admin_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["admin_block"], callback_data="admin_block"),
        InlineKeyboardButton(text=locale["admin_ignore"], callback_data="admin_ignore")
    )
    return kb


def action_announcement_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_publish"], callback_data="publish_announcement"))
    kb.add(InlineKeyboardButton(text=locale["button_preview"], callback_data="preview_announcement"))
    kb.add(InlineKeyboardButton(text=locale["button_cancel"], callback_data="cancel_announcement"))
    return kb


def preview_announcement_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="preview_back"))
    return kb
