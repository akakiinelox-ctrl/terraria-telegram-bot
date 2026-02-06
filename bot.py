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
# user_id -> {"menu": str, "boss": str, "npc": str}
user_state = {}

# ---------- KEYBOARDS ----------

def main_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "👁 Боссы",
        "🧑 NPC",
        "📘 О боте"
    )

# ----- BOSSES -----

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

# ----- NPC -----

def npc_list():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for npc in NPCS.values():
        kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb

def npc_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🏠 Дом")
    kb.add("🧩 Условия появления", "🛒 Услуги")
    kb.add("💡 Советы")
    kb.add("⬅ К NPC", "🏠 Главное меню")
    return kb

# ---------- HANDLERS ----------

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state[m.from_user.id] = {"menu": "main"}
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбери раздел 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\n"
        "Полноценный справочник по боссам и NPC Terraria.\n"
        "Создан для новичков.",
        reply_markup=main_menu()
    )

# ---------- BOSSES FLOW ----------

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"menu": "boss_stages"}
    await m.answer(
        "Выбери этап:",
        reply_markup=bosses_stage_menu()
    )

@dp.message_handler(lambda m: m.text == "🌱 Начало приключения")
async def pre_hardmode(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer(
        "🌱 Начало приключения — боссы:",
        reply_markup=bosses_list("Дохардмод")
    )

@dp.message_handler(lambda m: m.text == "⚙️ Хардмод")
async def hardmode(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer(
        "⚙️ Хардмод — боссы:",
        reply_markup=bosses_list("Хардмод")
    )

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def select_boss(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id]["boss"] = key
            user_state[m.from_user.id]["menu"] = "boss"
            await m.answer(
                f"{boss['name']}\n\n"
                f"Сложность: {boss['difficulty']}\n"
                f"Этап: {boss['stage']}",
                reply_markup=boss_menu()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "🛡 Подготовка", "🏗 Арена", "⚔ Оружие",
    "🧠 Тактика", "🔥 Опасности", "🎁 Зачем убивать"
])
async def boss_section(m: types.Message):
    uid = m.from_user.id
    if "boss" not in user_state.get(uid, {}):
        return

    boss = BOSSES[user_state[uid]["boss"]]
    section_map = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }

    await m.answer(
        boss["sections"][section_map[m.text]],
        reply_markup=boss_menu()
    )

@dp.message_handler(lambda m: m.text == "⬅ К списку боссов")
async def back_to_bosses(m: types.Message):
    await bosses(m)

# ---------- NPC FLOW ----------

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_start(m: types.Message):
    user_state[m.from_user.id] = {"menu": "npc_list"}
    await m.answer(
        "🧑 NPC — выбери персонажа:",
        reply_markup=npc_list()
    )

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def select_npc(m: types.Message):
    for key, npc in NPCS.items():
        if m.text == npc["name"]:
            user_state[m.from_user.id]["npc"] = key
            user_state[m.from_user.id]["menu"] = "npc"
            await m.answer(
                npc["name"],
                reply_markup=npc_menu()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "📖 Описание", "🏠 Дом", "🧩 Условия появления",
    "🛒 Услуги", "💡 Советы"
])
async def npc_section(m: types.Message):
    uid = m.from_user.id
    if "npc" not in user_state.get(uid, {}):
        return

    npc = NPCS[user_state[uid]["npc"]]
    section_map = {
        "📖 Описание": "description",
        "🧩 Условия появления": "requirements",
        "🏠 Дом": "housing",
        "🛒 Услуги": "services",
        "💡 Советы": "tips"
    }

    await m.answer(
        npc["sections"][section_map[m.text]],
        reply_markup=npc_menu()
    )

@dp.message_handler(lambda m: m.text == "⬅ К NPC")
async def back_to_npc(m: types.Message):
    await npc_start(m)

# ---------- BACK ----------

@dp.message_handler(lambda m: m.text in ["🏠 Главное меню", "⬅ Назад"])
async def back(m: types.Message):
    await start(m)

# ---------- RUN ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)