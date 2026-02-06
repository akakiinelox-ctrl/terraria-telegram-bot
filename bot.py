import json
import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =========================
# ДАННЫЕ
# =========================

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(e)
        return {}

BOSSES = load_json("data/bosses.json").get("pre_hardmode", {})

# =========================
# ПРОГРЕССИЯ
# =========================

NEXT_BOSS = {
    "Король слизней": "Глаз Ктулху",
    "Глаз Ктулху": "EVIL_BOSS",
    "Пожиратель миров": "Королева пчёл",
    "Мозг Ктулху": "Королева пчёл",
    "Королева пчёл": "Скелетрон",
    "Скелетрон": "Стена плоти",
    "Стена плоти": None
}

# =========================
# СОСТОЯНИЕ
# =========================

user_selected_boss = {}
user_favorites = {}

# =========================
# ВСПОМОГАТЕЛЬНЫЕ
# =========================

def difficulty_icon(text):
    if "Лёг" in text:
        return "🟢"
    if "Сред" in text:
        return "🟡"
    if "Слож" in text:
        return "🔴"
    return "⚪"

def boss_icon(name):
    return {
        "Король слизней": "👑",
        "Глаз Ктулху": "👁",
        "Пожиратель миров": "🐛",
        "Мозг Ктулху": "🧠",
        "Королева пчёл": "🐝",
        "Скелетрон": "💀",
        "Стена плоти": "🔥"
    }.get(name, "👁")

def get_favs(uid):
    return user_favorites.setdefault(uid, set())

# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "⭐ Избранное")
    return kb

def bosses_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    favs = get_favs(uid)
    for b in BOSSES.values():
        star = " ⭐" if b["name"] in favs else ""
        kb.add(f"{difficulty_icon(b['difficulty'])} {boss_icon(b['name'])} {b['name']}{star}")
    kb.add("🏠 Главное меню")
    return kb

def boss_menu(is_fav):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        "⚠️ Угрозы", "📋 Минимум",
        "🛡 Броня и ресурсы", "⚔️ Оружие",
        "🏗 Арена", "🎯 Поведение и урон",
        "❌ Ошибки", "🆘 Если сложно",
        "➡️ Следующий босс"
    )
    kb.add("⭐ Убрать из избранного" if is_fav else "⭐ В избранное")
    kb.add("⬅️ К боссам", "🏠 Главное меню")
    return kb

# =========================
# ХЕНДЛЕРЫ
# =========================

@dp.message_handler(commands=["start"])
async def start(m):
    await m.answer("🎮 Terraria Guide Bot", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m):
    await m.answer("Выбери босса:", reply_markup=bosses_menu(m.from_user.id))

@dp.message_handler(lambda m: any(b["name"] in m.text for b in BOSSES.values()))
async def select_boss(m):
    for b in BOSSES.values():
        if b["name"] in m.text:
            user_selected_boss[m.from_user.id] = b
            fav = b["name"] in get_favs(m.from_user.id)
            await m.answer(
                f"{difficulty_icon(b['difficulty'])} {boss_icon(b['name'])} {b['name']}\n{b['stage']}",
                reply_markup=boss_menu(fav)
            )
            return

@dp.message_handler(lambda m: m.text == "➡️ Следующий босс")
async def next_boss(m):
    boss = user_selected_boss.get(m.from_user.id)
    if not boss:
        await m.answer("Сначала выбери босса.")
        return

    nxt = NEXT_BOSS.get(boss["name"])
    if not nxt:
        await m.answer("Это последний босс перед Хардмодом.")
        return

    if nxt == "EVIL_BOSS":
        await m.answer(
            "➡️ Следующий босс:\n"
            "🐛 Пожиратель миров (Порча)\n"
            "🧠 Мозг Ктулху (Багрянец)\n\n"
            "Почему:\n"
            "Эти боссы дают руду и экипировку\n"
            "для дальнейшего прогресса."
        )
        return

    for b in BOSSES.values():
        if b["name"] == nxt:
            user_selected_boss[m.from_user.id] = b
            fav = b["name"] in get_favs(m.from_user.id)
            await m.answer(
                f"➡️ Следующий босс:\n\n"
                f"{difficulty_icon(b['difficulty'])} {boss_icon(b['name'])} {b['name']}\n\n"
                f"Почему:\n{b['progression_value']}",
                reply_markup=boss_menu(fav)
            )
            return

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def home(m):
    await m.answer("Главное меню:", reply_markup=main_menu())

@dp.message_handler()
async def fallback(m):
    await m.answer("Используй кнопки 👇", reply_markup=main_menu())

# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)