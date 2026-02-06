from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("👁 Боссы"))
    kb.add(KeyboardButton("⭐ Избранное"), KeyboardButton("📊 Прогресс"))
    return kb

def bosses_kb(bosses: dict):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for key, boss in bosses.items():
        kb.add(KeyboardButton(f"{boss['icon']} {boss['name']}"))
    kb.add(KeyboardButton("⬅ Назад"))
    return kb

def boss_actions_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("⭐ В избранное"))
    kb.add(KeyboardButton("✅ Пройден"))
    kb.add(KeyboardButton("⬅ Назад"))
    kb.add(KeyboardButton("🏠 Главное меню"))
    return kb