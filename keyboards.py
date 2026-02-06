from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("👁 Боссы"),
    KeyboardButton("📘 Прогрессия"),
    KeyboardButton("ℹ️ О боте")
)

def bosses_menu(bosses: list):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in bosses:
        kb.add(KeyboardButton(boss))
    kb.add(
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb