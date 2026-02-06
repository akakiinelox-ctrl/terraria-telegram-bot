import json
import os

from aiogram import Bot, Dispatcher, executor, types

from keyboards import main_menu_kb, bosses_kb, back_menu_kb

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# ---------- ВСПОМОГАТЕЛЬНОЕ ----------

def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clear_name(text: str) -> str:
    """
    Убирает эмодзи и лишние символы из кнопки,
    чтобы совпало с ключом в bosses.json
    """
    return (
        text.replace("🟢", "")
        .replace("🟡", "")
        .replace("🔴", "")
        .replace("🔥", "")
        .replace("👑", "")
        .replace("🐛", "")
        .replace("👁", "")
        .replace("🦴", "")
        .replace("🐝", "")
        .replace("🧠", "")
        .replace("🌙", "")
        .replace("💀", "")
        .strip()
        .lower()
    )


# ---------- ДАННЫЕ ----------

BOSSES = load_json("data/bosses.json")
PROGRESSION = load_json("data/progression.json")


# ---------- START / ГЛАВНОЕ МЕНЮ ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Полные гайды по Terraria.\n"
        "Используй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await start(message)


# ---------- БОССЫ ----------

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 *Выбери босса:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )


@dp.message_handler(lambda m: clear_name(m.text) in BOSSES)
async def show_boss_guide(message: types.Message):
    key = clear_name(message.text)
    boss = BOSSES[key]

    text = (
        f"{boss['icon']} *{boss['name']}*\n"
        f"{boss['difficulty']}\n\n"

        f"📍 *Этап:* {boss['stage']}\n\n"

        f"🎯 *Зачем убивать:*\n"
        f"{boss['why']}\n\n"

        f"📦 *Призыв:*\n"
        f"{boss['summon']}\n\n"

        f"🛡 *Рекомендуемая броня:*\n"
        f"{boss['armor']}\n\n"

        f"⚔️ *Оружие по классам:*\n"
        f"{boss['weapons']}\n\n"

        f"🏗 *Арена:*\n"
        f"{boss['arena']}\n\n"

        f"⚠️ *Опасности:*\n"
        f"{boss['dangers']}\n\n"

        f"🏆 *Дроп и польза:*\n"
        f"{boss['loot']}"
    )

    await message.answer(
        text,
        reply_markup=back_menu_kb(),
        parse_mode="Markdown"
    )


# ---------- ПРОГРЕСС ----------

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(message: types.Message):
    progress = PROGRESSION["pre_hardmode"]

    text = "📊 *Прогресс (Дохардмод)*\n\n"
    for boss in progress:
        text += f"❌ {boss}\n"

    await message.answer(
        text,
        reply_markup=back_menu_kb(),
        parse_mode="Markdown"
    )


# ---------- ИЗБРАННОЕ (заглушка) ----------

@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def favorites(message: types.Message):
    await message.answer(
        "⭐ *Избранное*\n\n"
        "Пока в разработке 👷",
        reply_markup=back_menu_kb(),
        parse_mode="Markdown"
    )


# ---------- FALLBACK ----------

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer(
        "Используй кнопки 👇",
        reply_markup=main_menu_kb()
    )


# ---------- ЗАПУСК ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)