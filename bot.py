import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

BOSSES = load("data/bosses.json")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Команда:\n"
        "/boss eye of cthulhu"
    )

@dp.message(Command("boss"))
async def boss(message: types.Message):
    name = message.text.replace("/boss", "").strip().lower()
    if name not in BOSSES:
        await message.answer("❌ Босс не найден")
        return

    b = BOSSES[name]
    await message.answer(
        f"👁 {name.title()}\n"
        f"❤️ HP: {b['hp']}\n"
        f"🧿 Призыв: {b['summon']}\n"
        f"⚔️ Тактика: {b['strategy']}"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
