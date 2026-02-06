import json
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ================== TOKEN ==================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "TOKEN_ТУТ"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================== LOAD DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/progression.json", encoding="utf-8") as f:
    PROGRESSION = json.load(f)

# ================== MAP ИМЁН → KEY ==================
BOSS_NAME_MAP = {
    "Король слизней": "king_slime",
    "Глаз Ктулху": "eye_of_cthulhu",
    "Пожиратель миров": "eater_of_worlds",
    "Мозг Ктулху": "brain_of_cthulhu",
    "Королева пчёл": "queen_bee",
    "Скелетрон": "skeletron",
    "Стена плоти": "wall_of_flesh",
}

# ================== KEYBOARDS ==================
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("⭐ Избранное", "📊 Прогресс")
    return kb


def bosses_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        kb.add(boss["name"])
    kb.add("🏠 Главное меню")
    return kb


# ================== START / AUTO START ==================
@dp.message_handler(commands=["start"])
@dp.message_handler(lambda m: m.text in ("🏠 Главное меню",))
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Полные гайды по боссам.\n"
        "Используй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


# ================== BOSSES MENU ==================
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 Выбери босса:",
        reply_markup=bosses_kb()
    )


# ================== BOSS GUIDE ==================
@dp.message_handler(lambda m: any(name in m.text for name in BOSS_NAME_MAP))
async def boss_guide(message: types.Message):
    boss_key = None
    for name, key in BOSS_NAME_MAP.items():
        if name in message.text:
            boss_key = key
            break

    if not boss_key:
        await message.answer("❌ Босс не найден")
        return

    boss = BOSSES[boss_key]

    text = (
        f"🔥 *{boss['name']}*\n"
        f"⚙ Стадия: {boss['stage']}\n"
        f"⚔ Сложность: {boss['difficulty']}\n\n"

        f"🚨 *Угрозы:*\n{boss['threat_profile']}\n\n"
        f"❤️ *Минимум:* {boss['minimum_requirements']}\n"
        f"🛡 *Броня:* {boss['recommended_armor']}\n"
        f"📦 *Ресурсы:* {boss['required_resources']}\n\n"

        f"⚔ *Оружие по классам:*\n"
        f"• Воин: {boss['weapons']['warrior']}\n"
        f"• Стрелок: {boss['weapons']['ranger']}\n"
        f"• Маг: {boss['weapons']['mage']}\n"
        f"• Призыватель: {boss['weapons']['summoner']}\n\n"

        f"🏗 *Арена:* {boss['arena_blueprint']}\n"
        f"🧠 *Поведение:* {boss['boss_behavior']}\n"
        f"💥 *Окна урона:* {boss['damage_windows']}\n"
        f"❌ *Частые ошибки:* {boss['common_failures']}\n"
        f"🛠 *Как исправить:* {boss['recovery_plan']}\n\n"
        f"📈 *Прогресс:* {boss['progression_value']}"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=bosses_kb()
    )


# ================== PROGRESS ==================
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(message: types.Message):
    completed = PROGRESSION.get("Дохардмод", [])
    total = len(BOSSES)

    bar = "■" * len(completed) + "□" * (total - len(completed))

    text = (
        f"📊 *Прогресс*\n"
        f"[{bar}] {int(len(completed)/total*100)}%\n\n" +
        "\n".join(f"❌ {b}" for b in completed)
    )

    await message.answer(text, parse_mode="Markdown")


# ================== FAVORITES ==================
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def favorites(message: types.Message):
    await message.answer(
        "⭐ Избранное\n\n(пока в разработке)",
        reply_markup=main_menu_kb()
    )


# ================== FALLBACK ==================
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer(
        "Используй кнопки 👇",
        reply_markup=main_menu_kb()
    )


# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)