import json
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import executor

from keyboards import main_menu, bosses_keyboard


BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# ---------- utils ----------

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_name(text: str) -> str:
    """
    Убираем эмодзи и лишние символы
    """
    text = re.sub(r"[^\w\sА-Яа-яЁё]", "", text)
    return text.strip().lower()


# ---------- data ----------

BOSSES = load_json("data/bosses.json")


# ---------- handlers ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide*\n\n"
        "Полноценные гайды по боссам, прогрессу и подготовке.\n"
        "Используй кнопки ниже 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def show_bosses(message: types.Message):
    await message.answer(
        "Выбери босса:",
        reply_markup=bosses_keyboard()
    )


@dp.message_handler()
async def boss_guide(message: types.Message):
    key = clear_name(message.text)

    if key not in BOSSES:
        return  # игнорируем лишний текст, чтобы не было мусора и крашей

    b = BOSSES[key]

    text = (
        f"{b['icon']} *{b['name']}*\n"
        f"{b['difficulty']}\n\n"

        f"📍 *Этап:* {b['stage']}\n"
        f"🎯 *Зачем убивать:*\n{b['why']}\n\n"

        f"📦 *Призыв:*\n{b['summon']}\n\n"

        f"🛡 *Рекомендуемая броня:*\n{b['armor']}\n\n"
        f"⚔️ *Оружие по классам:*\n{b['weapons']}\n\n"

        f"🏗 *Арена:*\n{b['arena']}\n\n"
        f"⚠️ *Опасности:*\n{b['dangers']}\n\n"

        f"🏆 *Награды:*\n{b['loot']}"
    )

    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ---------- run ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)