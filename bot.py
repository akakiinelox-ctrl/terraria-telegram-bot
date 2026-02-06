import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# =====================
# ИНИЦИАЛИЗАЦИЯ
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================
# КНОПКИ
# =====================

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢 Дохардмод", callback_data="prehard")],
    [InlineKeyboardButton(text="🔥 Хардмод (скоро)", callback_data="hard_stub")],
    [InlineKeyboardButton(text="📘 Общие советы (скоро)", callback_data="guide_stub")]
])

prehard_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👁 Глаз Ктулху", callback_data="eye")],
    [InlineKeyboardButton(text="🐝 Королева пчёл", callback_data="bee")],
    [InlineKeyboardButton(text="💀 Скелетрон", callback_data="skeletron")],
    [InlineKeyboardButton(text="🧱 Стена плоти", callback_data="wall")],
    [InlineKeyboardButton(text="⬅ Назад", callback_data="back")]
])

# =====================
# /start
# =====================

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🎮 **Terraria Guide Bot**\n\n"
        "Полноценные гайды по прогрессии Terraria.\n\n"
        "Выбери этап игры:",
        reply_markup=main_menu,
        parse_mode="Markdown"
    )

# =====================
# НАВИГАЦИЯ
# =====================

@dp.callback_query(lambda c: c.data == "prehard")
async def open_prehard(callback: CallbackQuery):
    await callback.message.edit_text(
        "🟢 **Дохардмод**\n\n"
        "Боссы до Хардмода:",
        reply_markup=prehard_menu,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 **Terraria Guide Bot**\n\nВыбери этап:",
        reply_markup=main_menu,
        parse_mode="Markdown"
    )

# =====================
# ГЛАЗ КТУЛХУ
# =====================

@dp.callback_query(lambda c: c.data == "eye")
async def eye(callback: CallbackQuery):
    await callback.message.answer(
        "👁 **Глаз Ктулху**\n\n"
        "**Описание:**\n"
        "Первый серьёзный босс Terraria. Проверяет мобильность и подготовку игрока.\n\n"

        "**Условия появления:**\n"
        "• Использовать *Глаз подозрения* ночью\n"
        "• Может появиться сам при 200+ HP и 10+ защиты\n\n"

        "**Подготовка:**\n"
        "• Арена из 2–3 рядов платформ\n"
        "• Зелья: скорость, регенерация, железная кожа\n"
        "• Обувь с ускорением\n\n"

        "**Оружие по классам:**\n"
        "🗡 Воин: Зачарованный бумеранг\n"
        "🏹 Стрелок: Лук + огненные стрелы\n"
        "🔮 Маг: Самоцветный посох\n"
        "🐲 Призыватель: Посох слизи\n\n"

        "**Тактика боя:**\n"
        "1. Первая фаза — уклоняйся и стреляй\n"
        "2. Вторая фаза — агрессивные рывки\n"
        "3. Никогда не стой на месте\n\n"

        "**Частые ошибки:**\n"
        "• Бой без арены\n"
        "• Недостаток скорости\n\n"

        "**Награды:**\n"
        "• Демонитовая/Кримтановая руда\n"
        "• Материалы для снаряжения\n\n"

        "**После победы:**\n"
        "➡ Открывается путь к следующим боссам",
        parse_mode="Markdown"
    )

# =====================
# КОРОЛЕВА ПЧЁЛ
# =====================

@dp.callback_query(lambda c: c.data == "bee")
async def bee(callback: CallbackQuery):
    await callback.message.answer(
        "🐝 **Королева пчёл**\n\n"
        "**Описание:**\n"
        "Опасный босс джунглей, атакующий роем и ядом.\n\n"

        "**Призыв:**\n"
        "• Уничтожить личинку в улье\n\n"

        "**Подготовка:**\n"
        "• Арена в улье или снаружи\n"
        "• Защита от яда обязательна\n\n"

        "**Тактика:**\n"
        "• Средняя дистанция\n"
        "• Уклонение важнее урона\n\n"

        "**Награды:**\n"
        "• Пчелиные предметы\n"
        "• Доступ к Слизневой королеве позже",
        parse_mode="Markdown"
    )

# =====================
# СКЕЛЕТРОН
# =====================

@dp.callback_query(lambda c: c.data == "skeletron")
async def skeletron(callback: CallbackQuery):
    await callback.message.answer(
        "💀 **Скелетрон**\n\n"
        "**Описание:**\n"
        "Хранитель Данжа. Быстрый и смертельно опасный.\n\n"

        "**Призыв:**\n"
        "• Поговорить со Стариком ночью\n\n"

        "**Тактика:**\n"
        "• Сначала уничтожить руки\n"
        "• Высокая мобильность\n\n"

        "**После победы:**\n"
        "➡ Открывается Данж",
        parse_mode="Markdown"
    )

# =====================
# СТЕНА ПЛОТИ
# =====================

@dp.callback_query(lambda c: c.data == "wall")
async def wall(callback: CallbackQuery):
    await callback.message.answer(
        "🧱 **Стена плоти**\n\n"
        "**Описание:**\n"
        "Финальный босс Дохардмода.\n\n"

        "**Призыв:**\n"
        "• Бросить куклу вуду гида в лаву\n\n"

        "**Подготовка:**\n"
        "• Длинная дорога в аду\n"
        "• Пробивающее оружие\n\n"

        "**ВАЖНО:**\n"
        "🔥 После победы начинается **Хардмод**",
        parse_mode="Markdown"
    )

# =====================
# ЗАГЛУШКИ
# =====================

@dp.callback_query(lambda c: c.data.endswith("stub"))
async def stub(callback: CallbackQuery):
    await callback.message.answer("⏳ Раздел в разработке")

# =====================
# ЗАПУСК
# =====================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())