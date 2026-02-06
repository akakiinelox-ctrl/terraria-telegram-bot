import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ===== ЗАГРУЗКА ДАННЫХ =====
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

BOSS_NAMES = [boss["name"] for boss in BOSSES.values()]

# ===== КНОПКИ =====
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("ℹ️ О боте")
    return kb

def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in BOSS_NAMES:
        kb.add(name)
    kb.add("⬅ Назад")
    return kb

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Гайды по боссам Terraria.\n"
        "Выбирай кнопками 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ===== О БОТЕ =====
@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about(message: types.Message):
    await message.answer(
        "📖 *Terraria Guide Bot*\n\n"
        "Подробные гайды по боссам Terraria.\n"
        "Без спойлеров, удобно для новичков.\n\n"
        "Навигация полностью кнопочная.",
        parse_mode="Markdown"
    )

# ===== БОССЫ =====
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 *Выбери босса:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )

# ===== ГАЙД ПО БОССУ =====
@dp.message_handler(lambda m: m.text in BOSS_NAMES)
async def boss_guide(message: types.Message):
    boss = next(b for b in BOSSES.values() if b["name"] == message.text)

    text = (
        f"*{boss['name']}*\n\n"
        f"⚔ *Сложность:* {boss['difficulty']}\n"
        f"🧱 *Этап:* {boss['stage']}\n\n"
        f"⚠️ *Опасности:*\n{boss['threat_profile']}\n\n"
        f"🛡 *Подготовка:*\n{boss['minimum_requirements']}\n\n"
        f"🛡 *Броня:*\n{boss['recommended_armor']}\n\n"
        f"📦 *Ресурсы:*\n{boss['required_resources']}\n\n"
        f"⚔ *Оружие:*\n"
        f"• Воин: {boss['weapons']['warrior']}\n"
        f"• Стрелок: {boss['weapons']['ranger']}\n"
        f"• Маг: {boss['weapons']['mage']}\n"
        f"• Призыватель: {boss['weapons']['summoner']}\n\n"
        f"🏗 *Арена:*\n{boss['arena_blueprint']}\n\n"
        f"🧠 *Тактика:*\n{boss['boss_behavior']}\n\n"
        f"🎁 *Зачем убивать:*\n{boss['progression_value']}"
    )

    await message.answer(
        text,
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )

# ===== НАЗАД =====
@dp.message_handler(lambda m: m.text == "⬅ Назад")
async def back(message: types.Message):
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_kb()
    )

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)