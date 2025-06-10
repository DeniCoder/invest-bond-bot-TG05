import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import BOT_TOKEN
from filters import get_bonds_with_filters

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

user_filters = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в бот для анализа облигаций MOEX!\n\n"
        "Выберите способ поиска:",
        reply_markup=main_menu
    )

@dp.message(F.text == "🔎 Поиск по тикеру")
async def request_ticker(message: Message):
    await message.answer("Введите тикер облигации (например, RU000A10B9Q9):")

@dp.message(F.text == "⚙️ Фильтр по параметрам")
async def show_filters(message: Message):
    await message.answer("Выберите параметры фильтрации:", reply_markup=filter_menu)

@dp.callback_query(F.data.startswith('filter_'))
async def process_filter_selection(callback_query: CallbackQuery):
    prompts = {
        "filter_rating": "Введите кредитный рейтинг (например, A или BBB):",
        "filter_coupon": "Введите минимальную купонную доходность (%):",
        "filter_yield": "Введите минимальную доходность к погашению (%):",
        "filter_maturity": "Введите максимальный срок до погашения (лет):"
    }
    user_filters['current_filter'] = callback_query.data
    await bot.send_message(callback_query.from_user.id, prompts[callback_query.data])
    await callback_query.answer()

@dp.callback_query(F.data == "apply_filters")
async def apply_filters(callback_query: CallbackQuery):
    # собираем только активные фильтры
    filters = {k: v for k, v in user_filters.items() if k != 'current_filter'}
    await bot.send_message(callback_query.from_user.id, "Ищу облигации…")
    bonds = get_bonds_with_filters(**filters)
    if not bonds:
        await bot.send_message(callback_query.from_user.id, "Не найдено облигаций по заданным критериям")
        await callback_query.answer()
        return

    text = [f"Найдено {len(bonds)} облигаций:\n"]
    for b in bonds:
        text.append(
            f"📊 {b['SECID']} – {b.get('SHORTNAME','')}\n"
            f"   🏛 {b.get('SECNAME','')}, 💰 {b.get('FACEVALUE','')} {b.get('CURRENCYID','')}\n"
            f"   📅 {b.get('MATDATE','')}, 📈 {b.get('COUPONVALUE','')}%\n"
            f"   📉 {b.get('YIELD','') or b.get('EFFECTIVEYIELD','')}%\n"
            f"   🏷 {b.get('CREDITRATING','')}\n"
        )
    await bot.send_message(callback_query.from_user.id, "\n".join(text))
    await callback_query.answer()

@dp.message(~F.text.in_(["🔎 Поиск по тикеру", "⚙️ Фильтр по параметрам"]))
async def process_input(message: Message):
    if 'current_filter' in user_filters:
        cf = user_filters.pop('current_filter')
        text = message.text.strip()
        try:
            if cf == "filter_rating":
                user_filters['credit_rating'] = text.upper()
            elif cf == "filter_coupon":
                user_filters['min_coupon'] = float(text.replace(',', '.'))
            elif cf == "filter_yield":
                user_filters['min_yield'] = float(text.replace(',', '.'))
            elif cf == "filter_maturity":
                user_filters['years_to_maturity'] = int(text)
        except ValueError:
            await message.answer("Неверный формат. Попробуйте ещё раз.")
            return
        await message.answer("Фильтр установлен. Продолжайте или примените фильтры:", reply_markup=filter_menu)
    else:
        ticker = message.text.strip().upper()
        # 1) данные по рынку
        url_market = f"https://iss.moex.com/iss/engines/stock/markets/bonds/securities/{ticker}.json"
        # 2) данные по эмитенту и рейтингу
        url_info   = f"https://iss.moex.com/iss/securities/{ticker}.json"
        try:
            r1 = requests.get(url_market, params={'iss.meta': 'off'}); r1.raise_for_status()
            r2 = requests.get(url_info,   params={'iss.meta': 'off'}); r2.raise_for_status()
            jm = r1.json().get('securities', {})
            cols, rows = jm.get('columns', []), jm.get('data', [])
            if not rows:
                await message.answer(f"Облигация {ticker} не найдена")
                return
            data = dict(zip(cols, rows[0]))

            js = r2.json().get('securities', {})
            cols2, rows2 = js.get('columns', []), js.get('data', [])
            info = dict(zip(cols2, rows2[0])) if rows2 else {}

            # marketdata для доходности
            md = r1.json().get('marketdata', {})
            mc, mr = md.get('columns', []), md.get('data', [])
            market = dict(zip(mc, mr[0])) if mr else {}
            yld = r1.json().get('marketdata_yields', {})
            yc, yr = yld.get('columns', []), yld.get('data', [])
            yields = dict(zip(yc, yr[0])) if yr else {}

            await message.answer(
                f"📊 Инфо по {ticker}:\n\n"
                f"🏛 Эмитент: {info.get('ISSUER','')}\n"
                f"💰 Номинал: {data.get('FACEVALUE','')} {data.get('CURRENCYID','')}\n"
                f"📅 Погашение: {data.get('MATDATE','')}\n"
                f"📈 Купон: {data.get('COUPONVALUE','')}%\n"
                f"📉 Доходность: {market.get('YIELD','') or yields.get('EFFECTIVEYIELD','')}%\n"
                f"🏷 Рейтинг: {info.get('CREDITRATING','')}\n"
                f"📦 Амортизация: {'Да' if data.get('AMORTIZATIONDATE') and data['AMORTIZATIONDATE']!='0000-00-00' else 'Нет'}\n"
                f"📂 Оферта: {'Да' if data.get('OFFERDATE') and data['OFFERDATE']!='0000-00-00' else 'Нет'}"
            )
        except Exception as e:
            print(f"Error: {e}")
            await message.answer("Ошибка при получении данных. Попробуйте позже.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
