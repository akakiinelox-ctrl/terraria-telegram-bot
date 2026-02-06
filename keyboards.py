from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ---------- ГЛАВНОЕ МЕНЮ ----------

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


# ---------- СПИСОК БОССОВ ----------

def bosses_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("🟢 👑 Король слизней"))
    kb.add(KeyboardButton("🟡 👁 Глаз Ктулху"))
    kb.add(KeyboardButton("🟡 🐛 Пожиратель миров"))
    kb.add(KeyboardButton("🟡 🐝 Королева пчёл"))
    kb.add(KeyboardButton("🔴 🦴 Скелетрон"))
    kb.add(KeyboardButton("🔴 🔥 Стена плоти"))

    kb.add(
        KeyboardButton("🏠 Главное меню")
    )

    return kb


# ---------- НАЗАД / МЕНЮ ----------

def back_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("👁 Боссы"),
        KeyboardButton("🏠 Главное меню")
    )

    return kb