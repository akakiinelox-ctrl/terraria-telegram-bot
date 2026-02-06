from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- ГЛАВНОЕ МЕНЮ ----------
def main_menu_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("👁 Боссы"),
        KeyboardButton("⭐ Избранное"),
        KeyboardButton("📊 Прогресс")
    )

# ---------- БОССЫ ----------
def bosses_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢👑 Король слизней")
    kb.add("🔴👁 Глаз Ктулху")
    kb.add("🟡🐛 Пожиратель миров")
    kb.add("🟣🧠 Мозг Ктулху")
    kb.add("🟠🐝 Королева пчёл")
    kb.add("⚪💀 Скелетрон")
    kb.add("🔴🔥 Стена плоти")
    kb.add("⬅ Назад")
    return kb