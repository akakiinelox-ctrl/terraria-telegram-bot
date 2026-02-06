import json
import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =====================
# НАСТРОЙКИ
# =====================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =====================
# ЗАГРУЗКА ДАННЫХ
# =====================

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {path}: {e}")
        return {}

def bosses_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    boss_icons = {
        "Король слизней": "👑",
        "Глаз Ктулху": "👁",
        "Пожиратель миров": "🐛",
        "Мозг Ктулху": "🧠",
        "Королева пчёл": "🐝",
        "Скелетрон": "💀",
        "Стена плоти": "🔥"
    }

    for boss in BOSSES.values():
        diff = boss.get("difficulty", "")
        if "Лёг" in diff:
            diff_icon = "🟢"
        elif "Сред" in diff:
            diff_icon = "🟡"
        elif "Слож" in diff:
            diff_icon = "🔴"
        else:
            diff_icon = "⚪"

        name = boss["name"]
        icon = boss_icons.get(name, "👁")

        kb.add(KeyboardButton(f"{diff_icon} {icon} {name}"))

    kb.add(
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

def bosses_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        icon = difficulty_icon(boss.get("difficulty", ""))
        kb.add(KeyboardButton(f"{icon} {boss['name']}"))
    kb.add(
        KeyboardButton("⬅️ Назад"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

def boss_sections():
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
        KeyboardButton("⬅️ К боссам"),
        KeyboardButton("🏠 Главное меню")
    )
    return kb

# =====================
# ХЕНДЛЕРЫ
# =====================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Справочник по боссам Terraria.\n"
        "Выбирай кнопками 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def home(message):
    await message.answer("Главное меню:", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def show_bosses(message):
    await message.answer(
        "👁 Боссы (Дохардмод)\n\n"
        "🟢 Лёгкий  🟡 Средний  🔴 Сложный",
        reply_markup=bosses_menu()
    )

@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back(message):
    await message.answer("Главное меню:", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "⬅️ К боссам")
async def back_to_bosses(message):
    await message.answer("Выбери босса:", reply_markup=bosses_menu())

@dp.message_handler(lambda m: any(b["name"] in m.text for b in BOSSES.values()))
async def select_boss(message):
    for boss in BOSSES.values():
        if boss["name"] in message.text:
            user_boss[message.from_user.id] = boss
            icon = difficulty_icon(boss.get("difficulty", ""))
            await message.answer(
                f"{icon} {boss['name']}\n"
                f"{boss['stage']}\n\n"
                "Выбери раздел:",
                reply_markup=boss_sections()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "⚠️ Угрозы", "📋 Минимум", "🛡 Броня и ресурсы", "⚔️ Оружие",
    "🏗 Арена", "🎯 Поведение и урон", "❌ Ошибки",
    "🆘 Если сложно", "➡️ Зачем убивать"
])
async def show_section(message):
    boss = user_boss.get(message.from_user.id)
    if not boss:
        await message.answer("Сначала выбери босса.", reply_markup=main_menu())
        return

    section_map = {
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

    text = section_map.get(message.text, "Нет данных")
    await message.answer(
        f"{message.text} — {boss['name']}\n\n{text}",
        reply_markup=boss_sections()
    )

@dp.message_handler()
async def fallback(message):
    await message.answer(
        "Используй кнопки 👇",
        reply_markup=main_menu()
    )

# =====================
# ЗАПУСК
# =====================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)