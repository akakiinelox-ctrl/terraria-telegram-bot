import json
import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from keyboards import main_menu, bosses_menu

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

BOSSES = load_json("data/bosses.json")
PROGRESSION = load_json("data/progression.json")

# ---------- START ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Полные гайды по Terraria.\n"
        "Используй кнопки 👇",
        reply_markup=main_menu
    )

# ---------- MAIN MENU ----------

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def go_home(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def show_bosses(message: types.Message):
    await message.answer(
        "Выбери босса:",
        reply_markup=bosses_menu(list(BOSSES.keys()))
    )

@dp.message_handler(lambda m: m.text == "📘 Прогрессия")
async def show_progression(message: types.Message):
    text = "📘 Прогрессия Terraria\n\n"
    for stage, bosses in PROGRESSION.items():
        text += f"🔹 {stage}\n"
        for b in bosses:
            text += f"• {b}\n"
        text += "\n"

    await message.answer(text, reply_markup=main_menu)

@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about(message: types.Message):
    await message.answer(
        "🤖 Terraria Guide Bot\n\n"
        "• Каноничные гайды\n"
        "• Без ручного ввода\n"
        "• Удобные кнопки\n"
        "• Сделано фанатом Terraria",
        reply_markup=main_menu
    )

# ---------- BOSSES ----------

@dp.message_handler(lambda m: m.text in BOSSES)
async def boss_guide(message: types.Message):
    b = BOSSES[message.text]

    text = (
        f"👁 {message.text}\n\n"
        f"📍 Стадия: {b['stage']}\n"
        f"❤️ HP: {b['hp']}\n\n"
        f"🌀 Призыв:\n{b['summon']}\n\n"
        f"🏗 Арена:\n{b['arena']}\n\n"
        f"⚔️ Тактика:\n{b['strategy']}\n\n"
        f"🎁 Дроп:\n{b['drops']}"
    )

    await message.answer(
        text,
        reply_markup=bosses_menu(list(BOSSES.keys()))
    )

# ---------- BACK ----------

@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back_to_bosses(message: types.Message):
    await message.answer(
        "Список боссов:",
        reply_markup=bosses_menu(list(BOSSES.keys()))
    )

# ---------- FALLBACK ----------

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer(
        "Используй кнопки 👇",
        reply_markup=main_menu
    )

# ---------- RUN ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)