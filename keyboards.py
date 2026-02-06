from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("👁️ Боссы"),
        KeyboardButton("⭐ Избранное"),
        KeyboardButton("📊 Прогресс")
    )

def bosses_kb(boss_names):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for name in boss_names:
        kb.add(KeyboardButton(name))
    kb.add(KeyboardButton("⬅️ Назад"))
    return kb

def boss_actions_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("⭐ В избранное"),
        KeyboardButton("✅ Пройден"),
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
