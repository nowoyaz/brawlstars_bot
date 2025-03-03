from aiogram.dispatcher.filters.state import State, StatesGroup

class AnnouncementState(StatesGroup):
    waiting_for_rules = State()
    waiting_for_photo = State()
    waiting_for_description = State()
    waiting_for_keyword = State()
    waiting_for_action = State()
    waiting_in_preview = State() 