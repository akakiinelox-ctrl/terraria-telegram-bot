import json
import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "YOUR_BOT_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD BOSSES ----------
with open("data/bosses.json", "r", encoding="utf-8") as f:
    BOSSES = json.load(f)

# ---------- KEYBOARDS ----------

def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    return kb


def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        kb.add(boss["name"])
    kb.add("🏠 Главное меню")
    return kb


def boss_sections_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("⚔️ Сложность и этап", "⚠️ Опасности")
    kb.row("🔰 Подготовка", "⚔️ Оружие")
    kb.row("🏗️ Арена", "🧠 Тактика")
    kb.row("🎁 Зачем убивать")
    kb.add("⬅️ Назад к боссам")
    kb.add("🏠 Главное меню")
    return kb


# ---------- STATE ----------
user_current_boss = {}


# ---------- HANDLERS ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 **Terraria Guide Bot**\n\n"
        "Полные гайды по боссам Terraria.\n"
        "Используй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    user_current_boss.pop(message.from_user.id, None)
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb())


@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def show_bosses(message: types.Message):
    await message.answer("👁 Выбери босса:", reply_markup=bosses_kb())


@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def select_boss(message: types.Message):
    for key, boss in BOSSES.items():
        if message.text == boss["name"]:
            user_current_boss[message.from_user.id] = key
            await message.answer(
                f"{boss['name']}\n\n"
                f"⚔️ Сложность: {boss['difficulty']}\n"
                f"🧱 Этап: {boss['stage']}\n\n"
                f"Выбери раздел гайда 👇",
                reply_markup=boss_sections_kb()
            )
            return


@dp.message_handler(lambda m: m.text == "⬅️ Назад к боссам")
async def back_to_bosses(message: types.Message):
    user_current_boss.pop(message.from_user.id, None)
    await message.answer("👁 Выбери босса:", reply_markup=bosses_kb())


@dp.message_handler(lambda m: m.text in [
    "🔰 Подготовка", "🏗️ Арена", "⚔️ Оружие",
    "🧠 Тактика", "⚠️ Опасности", "🎁 Зачем убивать",
    "⚔️ Сложность и этап"
])
async def show_section(message: types.Message):
    uid = message.from_user.id

    if uid not in user_current_boss:
        await message.answer("❗ Сначала выбери босса.")
        return

    boss = BOSSES[user_current_boss[uid]]
    sections = boss["sections"]

    mapping = {
        "🔰 Подготовка": "preparation",
        "🏗️ Арена": "arena",
        "⚔️ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "⚠️ Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill",
    }

    if message.text == "⚔️ Сложность и этап":
        await message.answer(
            f"⚔️ Сложность: {boss['difficulty']}\n"
            f"🧱 Этап: {boss['stage']}"
        )
        return

    key = mapping.get(message.text)
    if key and key in sections:
        await message.answer(sections[key])
    else:
        await message.answer("❗ Раздел недоступен.")


# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)