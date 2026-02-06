import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН_СЮДА"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================== DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

# display_name -> boss_key
BOSS_NAME_MAP = {
    boss["name"]: key for key, boss in BOSSES.items()
}

# user_id -> boss_key
user_current_boss = {}

# ================== KEYBOARDS ==================
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("ℹ️ О боте")
    return kb

def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        kb.add(boss["name"])
    kb.add("🏠 Главное меню")
    return kb

def boss_sections_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "🛡 Подготовка",
        "🏗 Арена",
        "⚔ Оружие",
        "🧠 Тактика",
        "🔥 Смертельные угрозы",
        "❌ Частые ошибки",
        "🎁 Зачем убивать"
    )
    kb.add("⬅️ К боссам", "🏠 Главное меню")
    return kb

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Полноценный справочник по боссам Terraria.\n"
        "Выбирай кнопками 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ================== ABOUT ==================
@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about(message: types.Message):
    await message.answer(
        "📘 *Terraria Guide Bot*\n\n"
        "• Подробные гайды для новичков\n"
        "• Без полотен текста\n"
        "• Удобная кнопочная навигация\n\n"
        "Создан, чтобы реально помогать играть.",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )

# ================== BOSSES LIST ==================
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 *Выбери босса:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )

# ================== BOSS SELECT ==================
@dp.message_handler(lambda m: m.text in BOSS_NAME_MAP)
async def select_boss(message: types.Message):
    boss_key = BOSS_NAME_MAP[message.text]
    user_current_boss[message.from_user.id] = boss_key
    boss = BOSSES[boss_key]

    await message.answer(
        f"*{boss['name']}*\n\n"
        f"⚔ *Сложность:* {boss['difficulty']}\n"
        f"🧱 *Этап:* {boss['stage']}\n\n"
        "Выбери раздел гайда 👇",
        reply_markup=boss_sections_kb(),
        parse_mode="Markdown"
    )

# ================== SECTIONS ==================
@dp.message_handler(lambda m: m.text.startswith(
    ("🛡", "🏗", "⚔", "🧠", "🔥", "❌", "🎁")
))
async def boss_section(message: types.Message):
    uid = message.from_user.id
    if uid not in user_current_boss:
        return

    boss = BOSSES[user_current_boss[uid]]
    sections = boss["sections"]

    mapping = {
        "🛡 Подготовка": sections["preparation"],
        "🏗 Арена": sections["arena"],
        "⚔ Оружие": sections["weapons"],
        "🧠 Тактика": sections["tactics"],
        "🔥 Смертельные угрозы": sections["dangers"],
        "❌ Частые ошибки": sections["common_mistakes"],
        "🎁 Зачем убивать": sections["why_kill"]
    }

    text = mapping.get(message.text)
    if not text:
        return

    await message.answer(
        f"*{message.text}*\n\n{text}",
        parse_mode="Markdown",
        reply_markup=boss_sections_kb()
    )

# ================== NAVIGATION ==================
@dp.message_handler(lambda m: m.text == "⬅️ К боссам")
async def back_to_bosses(message: types.Message):
    user_current_boss.pop(message.from_user.id, None)
    await bosses_menu(message)

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def back_to_menu(message: types.Message):
    user_current_boss.pop(message.from_user.id, None)
    await message.answer(
        "🏠 *Главное меню:*",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)