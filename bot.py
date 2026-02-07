import json
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD DATA ----------

with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)

# ---------- STATE ----------
user_state = {}  # user_id -> dict

# ---------- KEYBOARDS ----------

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def bosses_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 Начало приключения")
    kb.add("⚙️ Хардмод")
    kb.add("⬅ Назад")
    return kb

def bosses_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        if boss["stage"] == stage:
            kb.add(boss["name"])
    kb.add("⬅ Назад")
    return kb

def boss_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку боссов", "🏠 Главное меню")
    return kb

def npc_list():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for npc in NPCS.values():
        kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb

def npc_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🧩 Условия появления")
    kb.add("🏠 Дом", "🛒 Услуги")
    kb.add("💡 Советы")
    kb.add("⬅ К NPC", "🏠 Главное меню")
    return kb

# ---------- HANDLERS ----------

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state[m.from_user.id] = {}
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбери раздел 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: "О боте" in m.text)
async def about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\n"
        "Полноценный справочник по боссам и NPC Terraria.\n"
        "Создан для новичков.",
        reply_markup=main_menu()
    )

# ---------- BOSSES ----------

@dp.message_handler(lambda m: "Боссы" in m.text)
async def bosses(m: types.Message):
    await m.answer("Выбери этап:", reply_markup=bosses_stage_menu())

@dp.message_handler(lambda m: "Начало приключения" in m.text)
async def pre_hardmode(m: types.Message):
    await m.answer(
        "🌱 Боссы начала игры:",
        reply_markup=bosses_list("Дохардмод")
    )

@dp.message_handler(lambda m: "Хардмод" in m.text)
async def hardmode(m: types.Message):
    await m.answer(
        "⚙️ Боссы Хардмода:",
        reply_markup=bosses_list("Хардмод")
    )

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def select_boss(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id]["boss"] = key
            await m.answer(
                f"{boss['name']}\n\n"
                f"Сложность: {boss['difficulty']}\n"
                f"Этап: {boss['stage']}",
                reply_markup=boss_menu()
            )
            return

@dp.message_handler(lambda m: any(x in m.text for x in [
    "Подготовка", "Арена", "Оружие",
    "Тактика", "Опасности", "Зачем"
]))
async def boss_section(m: types.Message):
    uid = m.from_user.id
    boss = BOSSES[user_state[uid]["boss"]]

    section_map = {
        "Подготовка": "preparation",
        "Арена": "arena",
        "Оружие": "weapons",
        "Тактика": "tactics",
        "Опасности": "dangers",
        "Зачем": "why_kill"
    }

    for key in section_map:
        if key in m.text:
            await m.answer(
                boss["sections"][section_map[key]],
                reply_markup=boss_menu()
            )
            return

# ---------- NPC ----------

@dp.message_handler(lambda m: "NPC" in m.text)
async def npc_start(m: types.Message):
    await m.answer("🧑 Выбери NPC:", reply_markup=npc_list())

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def select_npc(m: types.Message):
    for key, npc in NPCS.items():
        if m.text == npc["name"]:
            user_state[m.from_user.id]["npc"] = key
            await m.answer(npc["name"], reply_markup=npc_menu())
            return

@dp.message_handler(lambda m: any(x in m.text for x in [
    "Описание", "Условия", "Дом", "Услуги", "Советы"
]))
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["npc"]]

    section_map = {
        "Описание": "description",
        "Условия": "requirements",
        "Дом": "housing",
        "Услуги": "services",
        "Советы": "tips"
    }

    for key in section_map:
        if key in m.text:
            await m.answer(
                npc["sections"][section_map[key]],
                reply_markup=npc_menu()
            )
            return

# ---------- BACK ----------

@dp.message_handler(lambda m: "Назад" in m.text or "Главное" in m.text)
async def back(m: types.Message):
    await start(m)

# ---------- RUN ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)