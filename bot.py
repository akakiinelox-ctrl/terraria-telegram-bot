import os
import json
from aiogram import Bot, Dispatcher, executor, types

# ================== TOKEN ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в Railway Variables")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================== LOAD DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)["npcs"]

# ================== USER STATE ==================
user_state = {}  # user_id -> dict

# ================== KEYBOARDS ==================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def back_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add("⬅ Назад", "🏠 Главное меню")

def stages_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 До Хардмода", "⚙️ Хардмод")
    kb.add("⬅ Назад")
    return kb

def bosses_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        if boss["stage"] == stage:
            kb.add(boss["name"])
    kb.add("⬅ Назад")
    return kb

def boss_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку боссов", "🏠 Главное меню")
    return kb

def npc_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for npc in NPCS.values():
        if npc["stage"] == stage:
            kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb

def npc_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье и скидки")
    kb.add("💡 Советы")
    kb.add("⬅ К списку NPC", "🏠 Главное меню")
    return kb

# ================== HANDLERS ==================

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state[m.from_user.id] = {}
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбирай раздел 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\n"
        "Полный справочник по боссам и NPC Terraria.\n"
        "Создан для новичков и комфортного прохождения.",
        reply_markup=main_menu()
    )

# ---------- BOSSES ----------

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"menu": "boss_stage"}
    await m.answer("Выбери этап:", reply_markup=stages_menu())

@dp.message_handler(lambda m: m.text == "🌱 До Хардмода")
async def bosses_pre(m: types.Message):
    user_state[m.from_user.id]["stage"] = "Дохардмод"
    await m.answer("Боссы дохардмода:", reply_markup=bosses_list("Дохардмод"))

@dp.message_handler(lambda m: m.text == "⚙️ Хардмод")
async def bosses_hard(m: types.Message):
    user_state[m.from_user.id]["stage"] = "Хардмод"
    await m.answer("Боссы хардмода:", reply_markup=bosses_list("Хардмод"))

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_select(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id]["boss"] = key
            await m.answer(
                f"{boss['name']}\n\n"
                f"⚔ Сложность: {boss['difficulty']}\n"
                f"📍 Этап: {boss['stage']}",
                reply_markup=boss_sections()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "🛡 Подготовка", "🏗 Арена", "⚔ Оружие",
    "🧠 Тактика", "🔥 Опасности", "🎁 Зачем убивать"
])
async def boss_section(m: types.Message):
    boss = BOSSES[user_state[m.from_user.id]["boss"]]
    section_map = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }
    await m.answer(boss["sections"][section_map[m.text]], reply_markup=boss_sections())

@dp.message_handler(lambda m: m.text == "⬅ К списку боссов")
async def back_bosses(m: types.Message):
    stage = user_state[m.from_user.id]["stage"]
    await m.answer("Боссы:", reply_markup=bosses_list(stage))

# ---------- NPC ----------

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_menu(m: types.Message):
    user_state[m.from_user.id] = {"menu": "npc_stage"}
    await m.answer("NPC Terraria:", reply_markup=stages_menu())

@dp.message_handler(lambda m: m.text in ["🌱 До Хардмода", "⚙️ Хардмод"] and user_state.get(m.from_user.id, {}).get("menu") == "npc_stage")
async def npc_stage(m: types.Message):
    stage = "Дохардмод" if m.text == "🌱 До Хардмода" else "Хардмод"
    user_state[m.from_user.id]["npc_stage"] = stage
    await m.answer("NPC:", reply_markup=npc_list(stage))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_select(m: types.Message):
    for key, npc in NPCS.items():
        if m.text == npc["name"]:
            user_state[m.from_user.id]["npc"] = key
            await m.answer(
                f"{npc['name']}",
                reply_markup=npc_sections()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "📖 Описание", "🔓 Как получить", "🌍 Биом",
    "🏘️ Соседи", "😊 Счастье и скидки", "💡 Советы"
])
async def npc_section(m: types.Message):
    npc = NPCS[user_state[m.from_user.id]["npc"]]
    section_map = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье и скидки": "happiness",
        "💡 Советы": "tips"
    }
    await m.answer(npc["sections"][section_map[m.text]], reply_markup=npc_sections())

@dp.message_handler(lambda m: m.text == "⬅ К списку NPC")
async def back_npc(m: types.Message):
    stage = user_state[m.from_user.id]["npc_stage"]
    await m.answer("NPC:", reply_markup=npc_list(stage))

# ---------- BACK ----------

@dp.message_handler(lambda m: m.text in ["⬅ Назад", "🏠 Главное меню"])
async def back(m: types.Message):
    await start(m)

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)