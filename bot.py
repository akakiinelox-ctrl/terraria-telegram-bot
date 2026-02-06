# bot.py
import os
import json
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


BOSSES = load_json("data/bosses.json")


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Команды:\n"
        "/boss <имя босса>\n"
        "Пример: /boss eye of cthulhu"
    )


@dp.message(Command("boss"))
async def boss(message: types.Message):
    args = message.text.split(" ", 1)
    name = args[1].lower() if len(args) > 1 else ""

    if not name or name not in BOSSES:
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
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан (переменная окружения)")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())