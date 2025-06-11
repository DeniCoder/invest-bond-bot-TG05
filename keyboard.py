from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Создать основную клавиатуру"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по тикеру", callback_data="search_ticker")],
        [InlineKeyboardButton(text="📊 Поиск по фильтрам", callback_data="search_filters")],
        [InlineKeyboardButton(text="⚙️ Настроить фильтры", callback_data="setup_filters")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard

def get_filter_keyboard():
    """Создать клавиатуру для настройки фильтров"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Мин. купонная доходность", callback_data="set_min_yield")],
        [InlineKeyboardButton(text="📉 Макс. купонная доходность", callback_data="set_max_yield")],
        [InlineKeyboardButton(text="⏱️ Мин. дюрация (дни)", callback_data="set_min_duration")],
        [InlineKeyboardButton(text="⏰ Макс. дюрация (дни)", callback_data="set_max_duration")],
        [InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="reset_filters")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_setting_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настроить фильтры", callback_data="setup_filters")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_change_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить результаты", callback_data="search_filters")],
        [InlineKeyboardButton(text="⚙️ Изменить фильтры", callback_data="setup_filters")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard
