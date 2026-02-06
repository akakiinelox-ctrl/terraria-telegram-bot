import json
import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# НАСТРОЙКИ
# =========================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =========================
# ЗАГРУЗКА ДАННЫХ
# =========================

def load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {path}: {e}")
        return {}

DATA = load_json("data/bosses.json")
BOSSES = DATA.get("pre_hardmode", {})

# =========================
# СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ
# =========================

user_selected_boss = {}
user_favorites = {}  # user_id -> set(boss_name)

# =========================
# ВСПОМОГАТЕЛЬНЫЕ
# =========================

def difficulty_icon(text: str) -> str:
    if "Лёг" in text:
        return "🟢"
    if "Сред" in text:
        return "🟡"
    if "Слож" in text:
        return "🔴"
    return "⚪"

def boss_visual_icon(name: str) -> str:
    icons = {
        "Король слизней": "👑",
        "Глаз Ктулху": "👁",
        "Пожиратель миров": "🐛",
        "Мозг Ктулху": "🧠",
        "Королева пчёл": "🐝",
        "Скелетрон": "💀",
        "Стена плоти": "🔥"
    }
    return icons.get(name, "👁")

def get_favorites(user_id):
    return user_favorites.setdefault(user_id, set())

# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("👁 Боссы"),
        KeyboardButton("⭐ Избранное"),
        KeyboardButton("ℹ️ О боте")
    )
    return kb

def bosses_menu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    favs = get_favorites(user_id)

    for boss in BOSSES.values():
        diff = difficulty_icon(boss.get("difficulty", ""))
        icon = boss_visual_icon(boss["name"])
        star = " ⭐" if boss["name"] in favs else ""
        kb.add(KeyboardButton(f"{diff} {icon} {boss['name']}{star}"))

    kb.add(
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

def favorites_menu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    favs = get_favorites(user_id)

    if not favs:
        kb.add(KeyboardButton("⬅️ Назад"))
        return kb

    for name in favs:
        kb.add(KeyboardButton(f"⭐ {name}"))

    kb.add(
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

def boss_sections_menu(is_favorite: bool):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("⚠️ Угрозы"),
        KeyboardButton("📋 Минимум"),
        KeyboardButton("🛡 Броня и ресурсы"),
        KeyboardButton("⚔️ Оружие"),
        KeyboardButton("🏗 Арена"),
        KeyboardButton("🎯 Поведение и урон"),
        KeyboardButton("❌ Ошибки"),
        KeyboardButton("🆘 Если сложно"),
        KeyboardButton("➡️ Зачем убивать")
    )

    kb.add(
        KeyboardButton("⭐ Убрать из избранного" if is_favorite else "⭐ В избранное"),
        KeyboardButton("⬅️ К боссам"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

# =========================
# ХЕНДЛЕРЫ
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Справочник по боссам Terraria.\n"
        "Глубокие гайды с объяснениями.\n\n"
        "Выбирай кнопками 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def show_bosses(message: types.Message):
    await message.answer(
        "👁 Боссы (Дохардмод)\n\n"
        "🟢 Лёгкий   🟡 Средний   🔴 Сложный",
        reply_markup=bosses_menu(message.from_user.id)
    )

@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    favs = get_favorites(message.from_user.id)
    if not favs:
        await message.answer(
            "⭐ Избранное пусто.\n\n"
            "Добавь босса через его карточку.",
            reply_markup=main_menu()
        )
        return

    await message.answer(
        "⭐ Избранные боссы:",
        reply_markup=favorites_menu(message.from_user.id)
    )

@dp.message_handler(lambda m: any(b["name"] in m.text for b in BOSSES.values()))
async def select_boss(message: types.Message):
    for boss in BOSSES.values():
        if boss["name"] in message.text:
            user_selected_boss[message.from_user.id] = boss
            favs = get_favorites(message.from_user.id)
            is_fav = boss["name"] in favs

            diff = difficulty_icon(boss.get("difficulty", ""))
            icon = boss_visual_icon(boss["name"])

            await message.answer(
                f"{diff} {icon} {boss['name']}\n{boss['stage']}\n\nВыбери раздел:",
                reply_markup=boss_sections_menu(is_fav)
            )
            return

@dp.message_handler(lambda m: m.text in ["⭐ В избранное", "⭐ Убрать из избранного"])
async def toggle_favorite(message: types.Message):
    boss = user_selected_boss.get(message.from_user.id)
    if not boss:
        await message.answer("Сначала выбери босса.", reply_markup=main_menu())
        return

    favs = get_favorites(message.from_user.id)
    name = boss["name"]

    if name in favs:
        favs.remove(name)
        text = f"❌ {name} убран из избранного"
    else:
        favs.add(name)
        text = f"⭐ {name} добавлен в избранное"

    await message.answer(text, reply_markup=boss_sections_menu(name in favs))

@dp.message_handler(lambda m: m.text in [
    "⚠️ Угрозы", "📋 Минимум", "🛡 Броня и ресурсы", "⚔️ Оружие",
    "🏗 Арена", "🎯 Поведение и урон", "❌ Ошибки",
    "🆘 Если сложно", "➡️ Зачем убивать"
])
async def show_section(message: types.Message):
    boss = user_selected_boss.get(message.from_user.id)
    if not boss:
        await message.answer("Сначала выбери босса.", reply_markup=main_menu())
        return

    sections = {
        "⚠️ Угрозы": boss["threat_profile"],
        "📋 Минимум": boss["minimum_requirements"],
        "🛡 Броня и ресурсы": f"{boss['recommended_armor']}\n\nРесурсы:\n{boss['required_resources']}",
        "⚔️ Оружие": (
            f"🗡 Воин:\n{boss['weapons']['warrior']}\n\n"
            f"🏹 Стрелок:\n{boss['weapons']['ranger']}\n\n"
            f"🪄 Маг:\n{boss['weapons']['mage']}\n\n"
            f"🐲 Призыватель:\n{boss['weapons']['summoner']}"
        ),
        "🏗 Арена": boss["arena_blueprint"],
        "🎯 Поведение и урон": f"{boss['boss_behavior']}\n\nОкна урона:\n{boss['damage_windows']}",
        "❌ Ошибки": boss["common_failures"],
        "🆘 Если сложно": boss["recovery_plan"],
        "➡️ Зачем убивать": boss["progression_value"]
    }

    favs = get_favorites(message.from_user.id)
    is_fav = boss["name"] in favs

    await message.answer(
        f"{message.text} — {boss['name']}\n\n{sections.get(message.text, 'Нет данных')}",
        reply_markup=boss_sections_menu(is_fav)
    )

@dp.message_handler(lambda m: m.text in ["⬅️ Назад", "⬅️ К боссам"])
async def back(message: types.Message):
    await message.answer("Выбери босса:", reply_markup=bosses_menu(message.from_user.id))

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def home(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about(message: types.Message):
    await message.answer(
        "ℹ️ О боте\n\n"
        "• Справочник по Terraria\n"
        "• Гайды с объяснением «зачем и почему»\n"
        "• Vanilla Terraria 1.4.x\n\n"
        "⭐ Используй избранное, чтобы сохранять боссов.",
        reply_markup=main_menu()
    )

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Используй кнопки 👇", reply_markup=main_menu())

# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)