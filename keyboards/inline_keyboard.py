from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK, SUPPORT_LINK, MANAGER_LINK

def start_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_start"], callback_data="check_subscription"),
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
        InlineKeyboardButton(text=locale["button_filtered_search"], callback_data="show_filters_team"),
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
        InlineKeyboardButton(text=locale["button_filtered_search"], callback_data="show_filters_club"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu")
    )
    return kb

# Клавиатура подтверждения для обычного поиска
def confirmation_keyboard(locale, suffix="team"):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_okay"], callback_data=f"confirm_normal_search_{suffix}"))
    return kb


def report_confirmation_keyboard(locale, announcement_id, announcement_type, reason):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["confirm"], callback_data=f"confirm_report:{announcement_id}:{reason}:{announcement_type}:yes"),
        InlineKeyboardButton(text=locale["cancel"], callback_data=f"cancel_report:{announcement_id}:{announcement_type}")
    )
    return kb


def language_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_lang_ru"], callback_data="set_language:ru"),
        InlineKeyboardButton(text=locale["button_lang_eng"], callback_data="set_language:eng")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    return kb



def announcement_keyboard(locale, announcement_id, user_id, has_next, has_prev, announcement_type):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_write"], url=f"tg://user?id={user_id}"),
        InlineKeyboardButton(text=locale["button_report"], callback_data=f"report:{announcement_id}:{announcement_type}")
    )
    # Изменяем кнопку "Избранное", в обычном режиме должна быть "В избранное"
    if announcement_type == "favorites":
        kb.add(
            InlineKeyboardButton(text=locale["button_unfavorites"], callback_data=f"unfavorite:{announcement_id}:{announcement_type}")
        )
    else:
        kb.add(
            InlineKeyboardButton(text=locale["button_favorite"], callback_data=f"favorite:{announcement_id}:{announcement_type}")
        )
    
    # Добавляем кнопки навигации - "Назад" и "Далее"
    nav_buttons = []
    if has_prev:
        if announcement_type == "favorites":
            nav_buttons.append(InlineKeyboardButton(text="◀️ " + locale["button_prev"], callback_data="prev:favorites"))
        else:
            nav_buttons.append(InlineKeyboardButton(text="◀️ " + locale["button_prev"], callback_data=f"prev_{announcement_type}"))
    
    if has_next:
        if announcement_type == "favorites":
            nav_buttons.append(InlineKeyboardButton(text=locale["button_next"] + " ▶️", callback_data="next:favorites"))
        else:
            nav_buttons.append(InlineKeyboardButton(text=locale["button_next"] + " ▶️", callback_data=f"next_{announcement_type}"))
    
    # Добавляем кнопки в ряд, если есть хотя бы одна
    if nav_buttons:
        kb.row(*nav_buttons)
    
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
        kb.insert(InlineKeyboardButton(text=text, callback_data=f"confirm_report_selection:{announcement_id}:{reason}:{announcement_type}"))
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data=f"back_report:{announcement_id}:{announcement_type}"))
    return kb



# Клавиатура для фильтров поиска
def search_filters_keyboard(locale, announcement_type, filter_type=None):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text=locale["filter_new"], callback_data=f"filtered_search_{announcement_type}_new"),
        InlineKeyboardButton(text=locale["filter_old"], callback_data=f"filtered_search_{announcement_type}_old"),
        InlineKeyboardButton(text=locale["filter_premium"], callback_data=f"filtered_search_{announcement_type}_premium"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_search_menu")
    )
    return kb

def report_admin_keyboard(locale, reported_user_id, reporter_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["admin_block"], callback_data=f"admin_block:{reported_user_id}"),
        InlineKeyboardButton(text=locale["admin_ignore"], callback_data="admin_ignore")
    )
    kb.add(
        InlineKeyboardButton(text="Блокировать жалобщика", callback_data=f"admin_block_reporter:{reporter_id}")
    )
    return kb

def cancel_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="cancel_send_crystals"))
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


def keyword_selection_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["keyword_trophy_modes"], callback_data="keyword_trophy_modes"),
        InlineKeyboardButton(text=locale["keyword_ranked"], callback_data="keyword_ranked")
    )
    kb.add(
        InlineKeyboardButton(text=locale["keyword_club_events"], callback_data="keyword_club_events"),
        InlineKeyboardButton(text=locale["keyword_map_maker"], callback_data="keyword_map_maker")
    )
    kb.add(
        InlineKeyboardButton(text=locale["keyword_other"], callback_data="keyword_other")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_skip_keyword"], callback_data="skip_keyword")
    )
    return kb


def keyword_filter_keyboard(locale, announcement_type):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    # Добавляем кнопки только для команд
    if announcement_type == "team":
        # Добавляем кнопку для "Все" (без фильтра)
        buttons.append(InlineKeyboardButton(
            text=locale.get("filter_all_kw", "Все"),
            callback_data=f"keyword_filter:all:{announcement_type}"
        ))
        
        # Добавляем кнопки для каждого ключевого слова
        keywords = ["trophy_modes", "ranked", "club_events", "map_maker", "other"]
        for keyword in keywords:
            buttons.append(InlineKeyboardButton(
                text=locale.get(f"keyword_{keyword}", keyword.capitalize()),
                callback_data=f"keyword_filter:{keyword}:{announcement_type}"
            ))
        
        # Добавляем кнопки в клавиатуру
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.add(buttons[i], buttons[i+1])
            else:
                keyboard.add(buttons[i])
    
    # Кнопка "Назад"
    keyboard.add(InlineKeyboardButton(
        text=locale["button_back"],
        callback_data="back_to_search_options_menu" if announcement_type == "team" else "back_to_search_options_club_menu"
    ))
    
    return keyboard


def additional_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_language"], callback_data="language"),
        InlineKeyboardButton(text=locale["button_announcement_count"], callback_data="announcement_count")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_referral_program"], callback_data="referral"),
        InlineKeyboardButton(text=locale["button_favorites"], callback_data="favorites")
    )
    kb.add(
        InlineKeyboardButton(text=locale.get("button_achievements", "🏆 Достижения"), callback_data="achievements")
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_support"], url=SUPPORT_LINK)
    )
    kb.add(
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    return kb



def gift_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text=locale["button_receive_gift"], callback_data="receive_gift"),
        InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_main")
    )
    return kb

def rules_keyboard(locale, announcement_type: str):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text=locale["button_accept_rules"],
            callback_data=f"accept_rules_{announcement_type}"
        )
    )
    return kb

def premium_keyboard(locale, is_premium=False):
    kb = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка покупки премиума удалена по запросу пользователя
    
    # Добавляем кнопку информации о ценах 
    kb.add(InlineKeyboardButton(text=locale.get("premium_prices_info_button", "💰 Информация о ценах"), callback_data="premium_prices_info"))
    
    # Добавляем кнопку активации промокода
    kb.add(InlineKeyboardButton(text=locale.get("activate_promo_button", "🎟️ Активировать промокод"), callback_data="activate_promo"))
    
    # Добавляем кнопку связи с менеджером
    kb.add(InlineKeyboardButton(text=locale.get("contact_manager_button", "👨‍💼 Связаться с менеджером"), url=MANAGER_LINK))
    
    # Добавляем кнопку возврата в меню
    kb.add(InlineKeyboardButton(text=locale.get("button_back", "🔙 Назад в меню"), callback_data="back_to_main"))
    
    return kb

def premium_prices_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_contact_manager"], url=MANAGER_LINK))
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="premium"))
    return kb

def admin_premium_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=locale["button_change_month_price"], callback_data="change_price:month"))
    kb.add(InlineKeyboardButton(text=locale["button_change_half_year_price"], callback_data="change_price:half_year"))
    kb.add(InlineKeyboardButton(text=locale["button_change_year_price"], callback_data="change_price:year"))
    kb.add(InlineKeyboardButton(text=locale["button_change_forever_price"], callback_data="change_price:forever"))
    kb.add(InlineKeyboardButton(text=locale["button_back"], callback_data="back_to_admin"))
    return kb

def admin_panel_keyboard(locale):
    """Клавиатура для админ-панели"""
    kb = InlineKeyboardMarkup(row_width=1)
    
    kb.add(
        InlineKeyboardButton(text=locale.get("give_premium_button", "💎 Выдать премиум"), callback_data="give_premium"),
        InlineKeyboardButton(text=locale.get("premium_prices_button", "💵 Настройка цен"), callback_data="premium_prices"),
        InlineKeyboardButton(text=locale.get("manage_sponsors_button", "🔗 Управление спонсорами"), callback_data="manage_sponsors"),
        InlineKeyboardButton(text=locale.get("manage_promo_codes_button", "🎟️ Управление промокодами"), callback_data="manage_promo_codes")
    )
    
    return kb

def admin_premium_duration_keyboard(locale):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="1 месяц", callback_data="premium_1month"),
        InlineKeyboardButton(text="6 месяцев", callback_data="premium_6months")
    )
    kb.add(
        InlineKeyboardButton(text="1 год", callback_data="premium_1year"),
        InlineKeyboardButton(text="Навсегда", callback_data="premium_forever")
    )
    kb.add(InlineKeyboardButton(text=locale["back_to_admin_panel"], callback_data="back_to_admin"))
    return kb

# Клавиатуры для спонсоров
def sponsors_list_keyboard(locale, sponsors, user_id, user_subscriptions):
    """Клавиатура со списком спонсоров"""
    kb = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого спонсора
    for sponsor in sponsors:
        # Проверяем, подписан ли пользователь на спонсора
        is_subscribed = sponsor.id in user_subscriptions
        
        # Текст кнопки спонсора
        if is_subscribed:
            sponsor_text = f"✅ {sponsor.name}"
        else:
            sponsor_text = f"📣 {sponsor.name}"
        
        # Если пользователь уже подписан, кнопка будет неактивна
        if is_subscribed:
            kb.add(InlineKeyboardButton(
                text=sponsor_text,
                callback_data=f"sponsor_already_subscribed:{sponsor.id}"
            ))
        else:
            # Добавляем кнопку для проверки подписки
            kb.add(InlineKeyboardButton(
                text=sponsor_text,
                callback_data=f"check_subscription:{sponsor.id}"
            ))
            
            # Добавляем кнопку с прямой ссылкой на канал спонсора
            kb.add(InlineKeyboardButton(
                text=locale.get("go_to_channel", "🔗 Перейти на канал"),
                url=sponsor.link
            ))
    
    # Добавляем кнопку возврата в меню
    kb.add(InlineKeyboardButton(text=locale["back_to_menu"], callback_data="back_to_menu"))
    
    return kb

def admin_sponsors_keyboard(locale):
    """Клавиатура для управления спонсорами в админке"""
    kb = InlineKeyboardMarkup()
    
    # Кнопка добавления спонсора
    kb.add(InlineKeyboardButton(text=locale["admin_add_sponsor_button"], callback_data="add_sponsor"))
    
    # Кнопка возврата в админ-панель
    kb.add(InlineKeyboardButton(text=locale["back_to_admin_panel"], callback_data="back_to_admin"))
    
    return kb

def admin_sponsor_item_keyboard(locale, sponsor_id):
    """Клавиатура для управления отдельным спонсором"""
    kb = InlineKeyboardMarkup()
    
    # Кнопки управления спонсором
    kb.add(
        InlineKeyboardButton(
            text=locale["admin_toggle_sponsor_button"],
            callback_data=f"toggle_sponsor:{sponsor_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale["admin_delete_sponsor_button"],
            callback_data=f"delete_sponsor:{sponsor_id}"
        )
    )
    
    # Кнопка возврата к списку спонсоров
    kb.add(
        InlineKeyboardButton(
            text=locale["admin_back_to_sponsors"],
            callback_data="manage_sponsors"
        )
    )
    
    return kb

def admin_sponsor_confirm_delete_keyboard(locale, sponsor_id):
    """Клавиатура для подтверждения удаления спонсора"""
    kb = InlineKeyboardMarkup()
    
    # Кнопки подтверждения/отмены
    kb.row(
        InlineKeyboardButton(
            text=locale["confirm"],
            callback_data=f"confirm_delete_sponsor:{sponsor_id}"
        ),
        InlineKeyboardButton(
            text=locale["cancel"],
            callback_data=f"cancel_delete_sponsor:{sponsor_id}"
        )
    )
    
    return kb

def back_to_menu_keyboard(locale):
    """Клавиатура с кнопкой возврата в меню"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text=locale["back_to_menu"], callback_data="back_to_menu"))
    return kb

def achievements_keyboard(locale):
    """Клавиатура для раздела достижений"""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_my_achievements", "🏆 Мои достижения"), 
            callback_data="my_achievements"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_available_achievements", "🔍 Доступные достижения"), 
            callback_data="available_achievements"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_buy_achievement", "💰 Купить достижение"), 
            callback_data="buy_achievement"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_buy_secret", "🔍 Купить секретный контент"), 
            callback_data="secret_content"
        )
    )
    kb.add(
        InlineKeyboardButton(text=locale.get("button_back", "🔙 Назад"), callback_data="additional")
    )
    return kb

def back_to_achievements_keyboard(locale):
    """Клавиатура для возврата к списку достижений"""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_back_to_achievements", "🔙 К достижениям"), 
            callback_data="achievements"
        )
    )
    return kb

def buy_achievement_confirm_keyboard(locale, achievement_id):
    """Клавиатура для подтверждения покупки достижения"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_confirm_purchase", "✅ Купить"), 
            callback_data=f"confirm_buy_achievement:{achievement_id}"
        ),
        InlineKeyboardButton(
            text=locale.get("button_cancel", "❌ Отмена"), 
            callback_data="buy_achievement"
        )
    )
    return kb

def secret_content_keyboard(locale):
    """Клавиатура для секретного контента"""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_buy_secret_video", "🎬 Купить секретный ролик бубса (5000 монет)"), 
            callback_data="buy_secret_video"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_back_to_achievements", "🔙 К достижениям"), 
            callback_data="achievements"
        )
    )
    return kb

def confirm_secret_purchase_keyboard(locale, content_key):
    """Клавиатура для подтверждения покупки секретного контента"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(
            text=locale.get("button_confirm_purchase", "✅ Купить"), 
            callback_data=f"confirm_secret_purchase:{content_key}"
        ),
        InlineKeyboardButton(
            text=locale.get("button_cancel", "❌ Отмена"), 
            callback_data="secret_content"
        )
    )
    return kb
