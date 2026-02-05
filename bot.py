import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

BOSSES = load("data/bosses.json")

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Команды:\n"
        "/boss eye of cthulhu"
    )

@dp.message_handler(commands=["boss"])
async def boss(message: types.Message):
    name = message.get_args().lower()
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

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
