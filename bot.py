import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from filters import get_bonds_with_ticker, get_bonds_with_filters, format_bonds_list, MoexBondsAPI
from config import BOT_TOKEN
from keyboard import (
    get_main_keyboard, get_filter_keyboard, get_setting_keyboard, get_change_keyboard
)
from text import welcome_text, help_text, search_text, not_search_text


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для машины состояний
class BondStates(StatesGroup):
    waiting_for_ticker = State()
    waiting_for_min_yield = State()
    waiting_for_max_yield = State()
    waiting_for_min_duration = State()
    waiting_for_max_duration = State()

# Хранилище пользовательских фильтров
user_filters = {}

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    if user_id not in user_filters:
        user_filters[user_id] = {}

    text = welcome_text()
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    text = help_text()
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Обработчик кнопки помощи"""
    await help_handler(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "search_ticker")
async def search_ticker_callback(callback: CallbackQuery, state: FSMContext):
    """Начать поиск по тикеру"""
    await state.set_state(BondStates.waiting_for_ticker)

    text = search_text()
    await callback.message.edit_text(text)
    await callback.answer()

@dp.callback_query(F.data == "search_filters")
async def search_filters_callback(callback: CallbackQuery):
    """Поиск по фильтрам"""
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})

    if not filters:
        text = not_search_text()
        keyboard = get_setting_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text("🔄 Поиск облигаций...")

        try:
            # Добавляем стандартные фильтры
            search_filters = filters.copy()
            search_filters['status'] = 'A'  # Только активные
            search_filters['exclude_matured'] = True  # Исключить погашенные

            bonds = get_bonds_with_filters(search_filters)
            result_text = format_bonds_list(bonds, limit=5)

            keyboard = get_change_keyboard()

            await callback.message.edit_text(result_text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка при поиске облигаций: {e}")
            await callback.message.edit_text(
                f"❌ Ошибка при поиске облигаций: {str(e)}",
                reply_markup=get_main_keyboard()
            )

    await callback.answer()

@dp.callback_query(F.data == "setup_filters")
async def setup_filters_callback(callback: CallbackQuery):
    """Настройка фильтров"""
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})

    filter_text = "⚙️ Настройка фильтров поиска\n\n"
    filter_text += "Текущие настройки:\n"

    if filters:
        if 'min_coupon_percent' in filters:
            filter_text += f"📈 Мин. доходность: {filters['min_coupon_percent']}%\n"
        if 'max_coupon_percent' in filters:
            filter_text += f"📉 Макс. доходность: {filters['max_coupon_percent']}%\n"
        if 'min_duration' in filters:
            filter_text += f"⏱️ Мин. дюрация: {filters['min_duration']} дней\n"
        if 'max_duration' in filters:
            filter_text += f"⏰ Макс. дюрация: {filters['max_duration']} дней\n"
    else:
        filter_text += "Фильтры не настроены\n"

    filter_text += "\nВыберите параметр для настройки:"

    await callback.message.edit_text(filter_text, reply_markup=get_filter_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await start_handler(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "reset_filters")
async def reset_filters_callback(callback: CallbackQuery):
    """Сбросить фильтры"""
    user_id = callback.from_user.id
    user_filters[user_id] = {}

    await callback.message.edit_text(
        "✅ Все фильтры сброшены",
        reply_markup=get_filter_keyboard()
    )
    await callback.answer("Фильтры сброшены")

# Обработчики настройки фильтров
@dp.callback_query(F.data == "set_min_yield")
async def set_min_yield_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BondStates.waiting_for_min_yield)
    await callback.message.edit_text(
        "📈 Введите минимальную купонную доходность (%):\n"
        "Например: 20\n\n"
        "Отправьте /cancel для отмены"
    )
    await callback.answer()

@dp.callback_query(F.data == "set_max_yield")
async def set_max_yield_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BondStates.waiting_for_max_yield)
    await callback.message.edit_text(
        "📉 Введите максимальную купонную доходность (%):\n"
        "Например: 50\n\n"
        "Отправьте /cancel для отмены"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "set_min_duration")
async def set_min_duration_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BondStates.waiting_for_min_duration)
    await callback.message.edit_text(
        "⏱️ Введите минимальную дюрацию (дни):\n"
        "Например: 365\n\n"
        "Отправьте /cancel для отмены"
    )
    await callback.answer()

@dp.callback_query(F.data == "set_max_duration")
async def set_max_duration_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BondStates.waiting_for_max_duration)
    await callback.message.edit_text(
        "⏰ Введите максимальную дюрацию (дни):\n"
        "Например: 1000\n\n"
        "Отправьте /cancel для отмены"
    )
    await callback.answer()

# Обработчики ввода значений
@dp.message(BondStates.waiting_for_ticker)
async def process_ticker(message: Message, state: FSMContext):
    """Обработка ввода тикера"""
    ticker = message.text.strip().upper()

    await message.answer("🔄 Поиск информации об облигации...")

    try:
        bond_info = get_bonds_with_ticker(ticker)

        if bond_info:
            api = MoexBondsAPI()
            result_text = api.format_bond_info(bond_info)

            # Проверяем наличие кредитного рейтинга
            if not any(key.lower().find('rating') != -1 for key in bond_info.keys()):
                result_text += "\n\n⚠️ Информация о кредитном рейтинге не доступна через бесплатный API MOEX"
        else:
            result_text = f"❌ Облигация с тикером {ticker} не найдена"

        await message.answer(result_text, reply_markup=get_main_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при поиске облигации {ticker}: {e}")
        await message.answer(
            f"❌ Ошибка при поиске облигации: {str(e)}",
            reply_markup=get_main_keyboard()
        )

    await state.clear()

@dp.message(BondStates.waiting_for_min_yield)
async def process_min_yield(message: Message, state: FSMContext):
    try:
        value = float(message.text.strip())
        user_id = message.from_user.id

        if user_id not in user_filters:
            user_filters[user_id] = {}

        user_filters[user_id]['min_coupon_percent'] = value

        await message.answer(
            f"✅ Минимальная доходность установлена: {value}%",
            reply_markup=get_filter_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное число",
            reply_markup=get_filter_keyboard()
        )

    await state.clear()

@dp.message(BondStates.waiting_for_max_yield)
async def process_max_yield(message: Message, state: FSMContext):
    try:
        value = float(message.text.strip())
        user_id = message.from_user.id

        if user_id not in user_filters:
            user_filters[user_id] = {}

        user_filters[user_id]['max_coupon_percent'] = value

        await message.answer(
            f"✅ Максимальная доходность установлена: {value}%",
            reply_markup=get_filter_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное число",
            reply_markup=get_filter_keyboard()
        )

    await state.clear()

@dp.message(BondStates.waiting_for_min_duration)
async def process_min_duration(message: Message, state: FSMContext):
    try:
        value = int(message.text.strip())
        user_id = message.from_user.id

        if user_id not in user_filters:
            user_filters[user_id] = {}

        user_filters[user_id]['min_duration'] = value

        await message.answer(
            f"✅ Минимальная дюрация установлена: {value} дней",
            reply_markup=get_filter_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное число",
            reply_markup=get_filter_keyboard()
        )

    await state.clear()

@dp.message(BondStates.waiting_for_max_duration)
async def process_max_duration(message: Message, state: FSMContext):
    try:
        value = int(message.text.strip())
        user_id = message.from_user.id

        if user_id not in user_filters:
            user_filters[user_id] = {}

        user_filters[user_id]['max_duration'] = value

        await message.answer(
            f"✅ Максимальная дюрация установлена: {value} дней",
            reply_markup=get_filter_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное число",
            reply_markup=get_filter_keyboard()
        )

    await state.clear()

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard())

async def main():
    """Главная функция для запуска бота"""
    logger.info("Запуск бота...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
