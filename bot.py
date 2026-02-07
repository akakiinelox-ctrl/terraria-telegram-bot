import json
import os
from aiogram import Bot, Dispatcher, executor, types

# ================== TOKEN ==================
API_TOKEN = os.getenv("BOT_TOKEN", "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================== LOAD DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)

# ================== STATE ==================
user_state = {}  
# {
#   user_id: {
#       "menu": "main/boss_stage/boss_list/boss/npc_stage/npc_list/npc",
#       "boss": key,
#       "npc": key,
#       "npc_stage": "До Хардмода/Хардмод"
#   }
# }

# ================== KEYBOARDS ==================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def boss_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 До Хардмода", "⚙️ Хардмод")
    kb.add("🏠 Главное меню")
    return kb

def npc_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 NPC до Хардмода", "⚙️ NPC Хардмода")
    kb.add("🏠 Главное меню")
    return kb

def boss_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in BOSSES.values():
        if b["stage"] == stage:
            kb.add(b["name"])
    kb.add("⬅ Назад")
    return kb

def npc_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for n in NPCS.values():
        if n["stage"] == stage:
            kb.add(n["name"])
    kb.add("⬅ Назад")
    return kb

def boss_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def npc_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘 Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

# ================== START ==================

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state[m.from_user.id] = {"menu": "main"}
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбери раздел 👇",
        reply_markup=main_menu()
    )

# ================== ABOUT ==================

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\n"
        "Полный справочник по боссам и NPC Terraria.\n"
        "Сделано для новичков и прохождения без вики.",
        reply_markup=main_menu()
    )

# ================== BOSSES ==================

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"menu": "boss_stage"}
    await m.answer("Выбери этап:", reply_markup=boss_stage_menu())

@dp.message_handler(lambda m: m.text == "🌱 До Хардмода")
async def bosses_pre(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer("Боссы дохардмода:", reply_markup=boss_list("Дохардмод"))

@dp.message_handler(lambda m: m.text == "⚙️ Хардмод")
async def bosses_hard(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer("Боссы Хардмода:", reply_markup=boss_list("Хардмод"))

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def select_boss(m: types.Message):
    for k, b in BOSSES.items():
        if m.text == b["name"]:
            user_state[m.from_user.id]["boss"] = k
            user_state[m.from_user.id]["menu"] = "boss"
            await m.answer(
                f"{b['name']}\n\n"
                f"⚔ Сложность: {b['difficulty']}\n"
                f"📍 Этап: {b['stage']}",
                reply_markup=boss_menu()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "🛡 Подготовка", "🏗 Арена", "⚔ Оружие",
    "🧠 Тактика", "🔥 Опасности", "🎁 Зачем убивать"
])
async def boss_section(m: types.Message):
    uid = m.from_user.id
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

# ================== NPC ==================

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_root(m: types.Message):
    user_state[m.from_user.id] = {"menu": "npc_stage"}
    await m.answer("NPC Terraria:", reply_markup=npc_stage_menu())

@dp.message_handler(lambda m: m.text == "🌱 NPC до Хардмода")
async def npc_pre(m: types.Message):
    user_state[m.from_user.id]["menu"] = "npc_list"
    user_state[m.from_user.id]["npc_stage"] = "До Хардмода"
    await m.answer("NPC до Хардмода:", reply_markup=npc_list("До Хардмода"))

@dp.message_handler(lambda m: m.text == "⚙️ NPC Хардмода")
async def npc_hard(m: types.Message):
    user_state[m.from_user.id]["menu"] = "npc_list"
    user_state[m.from_user.id]["npc_stage"] = "Хардмод"
    await m.answer("NPC Хардмода:", reply_markup=npc_list("Хардмод"))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def select_npc(m: types.Message):
    for k, n in NPCS.items():
        if m.text == n["name"]:
            user_state[m.from_user.id]["npc"] = k
            user_state[m.from_user.id]["menu"] = "npc"
            await m.answer(n["name"], reply_markup=npc_menu())
            return

@dp.message_handler(lambda m: m.text in [
    "📖 Описание", "🔓 Как получить", "🌍 Биом",
    "🏘 Соседи", "😊 Счастье", "💡 Советы"
])
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["npc"]]

    section_map = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘 Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }

    await m.answer(
        npc["sections"][section_map[m.text]],
        reply_markup=npc_menu()
    )

# ================== BACK ==================

@dp.message_handler(lambda m: m.text == "⬅ К списку")
async def back_to_list(m: types.Message):
    uid = m.from_user.id
    if user_state.get(uid, {}).get("menu") == "npc":
        stage = user_state[uid]["npc_stage"]
        await m.answer(f"NPC {stage}:", reply_markup=npc_list(stage))
    else:
        await m.answer("Боссы:", reply_markup=boss_stage_menu())

@dp.message_handler(lambda m: m.text == "⬅ Назад")
async def back(m: types.Message):
    await start(m)

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def back_main(m: types.Message):
    await start(m)

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)