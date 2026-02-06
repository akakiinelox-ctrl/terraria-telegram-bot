# bot.py
import os
import json
import logging
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Берём токен из переменных окружения (Railway / Heroku / Vercel -> Environment variable)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_TOKEN = BOT_TOKEN.strip()  # убираем возможные пробелы и переносы

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Установи переменную окружения BOT_TOKEN без пробелов.")

if " " in BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN содержит пробелы — удали пробелы и вставь токен заново.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def load_json(path: str):
    """Загружает JSON файл, выбрасывает понятную ошибку если не найден/невалиден."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл данных не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Загружаем словарь боссов (ключи — в нижнем регистре)
try:
    BOSSES = load_json("data/bosses.json")
except Exception as e:
    logger.exception("Не удалось загрузить data/bosses.json")
    raise

# HELP / START
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎮 Terraria Guide Bot\n\n"
        "Команды:\n"
        "/boss <имя босса> — пример: /boss eye of cthulhu"
    )


# /boss handler
@dp.message(Command(commands=["boss"]))
async def cmd_boss(message: types.Message):
    # Надёжный парсинг аргументов: всё, что после "/boss"
    text = (message.text or "").strip()
    # Если команда была в формате "/boss@botname" — отрезаем первое слово
    args = text.split(" ", 1)
    name = args[1].strip().lower() if len(args) > 1 else ""

    if not name:
        await message.answer("❗ Использование: /boss <имя босса>\nПример: /boss eye of cthulhu")
        return

    if name not in BOSSES:
        await message.answer("❌ Босс не найден")
        return

    b = BOSSES[name]
    # Безопасно читаем поля
    hp = b.get("hp", "—")
    summon = b.get("summon", "—")
    strategy = b.get("strategy", "—")

    await message.answer(
        f"👁 {name.title()}\n"
        f"❤️ HP: {hp}\n"
        f"🧿 Призыв: {summon}\n"
        f"⚔️ Тактика: {strategy}"
    )


async def main():
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())