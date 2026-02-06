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
# ПРОГРЕССИЯ (ДОХАРДМОД)
# =========================

PROGRESSION_STEPS = [
    "Король слизней",
    "Глаз Ктулху",
    "EVIL_BOSS",  # Пожиратель миров ИЛИ Мозг Ктулху
    "Королева пчёл",
    "Скелетрон",
    "Стена плоти"
]

EVIL_BOSSES = {"Пожиратель миров", "Мозг Ктулху"}

# =========================
# СОСТОЯНИЕ
# =========================

user_selected_boss = {}
user_favorites = {}
user_defeated = {}  # user_id -> set(boss_name)

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

def get_defeated(uid):
    return user_defeated.setdefault(uid, set())

def progress_percent(uid):
    defeated = get_defeated(uid)
    done = 0

    for step in PROGRESSION_STEPS:
        if step == "EVIL_BOSS":
            if defeated & EVIL_BOSSES:
                done += 1
        elif step in defeated:
            done += 1

    return int(done / len(PROGRESSION_STEPS) * 100)

def progress_bar(percent):
    total = 10
    filled = int(percent / 10)
    return "█" * filled + "░" * (total - filled)

# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "⭐ Избранное")
    kb.add("📊 Прогресс")
    return kb

def bosses_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    favs = get_favs(uid)
    defeated = get_defeated(uid)

    for b in BOSSES.values():
        star = " ⭐" if b["name"] in favs else ""
        check = " ✔" if b["name"] in defeated else ""
        kb.add(f"{difficulty_icon(b['difficulty'])} {boss_icon(b['name'])} {b['name']}{star}{check}")

    kb.add("🏠 Главное меню")
    return kb

def boss_menu(uid, boss_name):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    defeated = get_defeated(uid)

    kb.add(
        "⚠️ Угрозы", "📋 Минимум",
        "🛡 Броня и ресурсы", "⚔️ Оружие",
        "🏗 Арена", "🎯 Поведение и урон",
        "❌ Ошибки", "🆘 Если сложно",
        "➡️ Следующий босс"
    )

    kb.add("☑️ Я победил этого босса" if boss_name not in defeated else "❌ Снять отметку")

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
            await m.answer(
                f"{difficulty_icon(b['difficulty'])} {boss_icon(b['name'])} {b['name']}\n{b['stage']}",
                reply_markup=boss_menu(m.from_user.id, b["name"])
            )
            return

@dp.message_handler(lambda m: m.text in ["☑️ Я победил этого босса", "❌ Снять отметку"])
async def toggle_defeated(m):
    boss = user_selected_boss.get(m.from_user.id)
    if not boss:
        await m.answer("Сначала выбери босса.")
        return

    defeated = get_defeated(m.from_user.id)
    name = boss["name"]

    if name in defeated:
        defeated.remove(name)
        text = f"❌ Снята отметка: {name}"
    else:
        defeated.add(name)
        text = f"✔ Победа засчитана: {name}"

    await m.answer(text, reply_markup=boss_menu(m.from_user.id, name))

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(m):
    percent = progress_percent(m.from_user.id)
    bar = progress_bar(percent)
    defeated = get_defeated(m.from_user.id)

    lines = []
    for step in PROGRESSION_STEPS:
        if step == "EVIL_BOSS":
            ok = "✔" if defeated & EVIL_BOSSES else "✖"
            lines.append(f"{ok} Пожиратель миров / Мозг Ктулху")
        else:
            ok = "✔" if step in defeated else "✖"
            lines.append(f"{ok} {step}")

    await m.answer(
        "📊 Прогресс (Дохардмод)\n\n"
        f"[{bar}] {percent}%\n\n" +
        "\n".join(lines),
        reply_markup=main_menu()
    )

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