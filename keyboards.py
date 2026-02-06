from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("👁 Боссы"),
        KeyboardButton("⭐ Избранное")
    )
    kb.add(
        KeyboardButton("📊 Прогресс")
    )
    return kb


def bosses_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🟢 👑 Король слизней")
    kb.add("🟡 👁 Глаз Ктулху")
    kb.add("🟡 🐛 Пожиратель миров")
    kb.add("🟡 🧠 Мозг Ктулху")
    kb.add("🟡 🐝 Королева пчёл")
    kb.add("🔴 🦴 Скелетрон")
    kb.add("🔴 🔥 Стена плоти")

    kb.add("🏠 Главное меню")
    return kb


def back_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("🏠 Главное меню")
    return kb