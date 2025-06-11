from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Поиск по тикеру")],
        [KeyboardButton(text="⚙️ Фильтр по параметрам")]
    ],
    resize_keyboard=True
)

filter_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏆 Кредитный рейтинг", callback_data="filter_rating")],
    [InlineKeyboardButton(text="📈 Мин. купонная доходность (%)", callback_data="filter_coupon")],
    [InlineKeyboardButton(text="📉 Мин. доходность к погашению (%)", callback_data="filter_yield")],
    [InlineKeyboardButton(text="📅 Срок до погашения (лет)", callback_data="filter_maturity")],
    [InlineKeyboardButton(text="✅ Применить фильтры", callback_data="apply_filters")]
])