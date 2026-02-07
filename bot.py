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

# ================== STATE ==================
user_state = {}  # user_id -> dict

# ================== KEYBOARDS ==================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb


def stage_menu(entity="boss"):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 До Хардмода")
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


def npc_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for npc in NPCS.values():
        if npc.get("stage", "Дохардмод") == stage:
            kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb


def boss_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("⚠ Опасности", "🎁 Зачем убивать")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb


def npc_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ Назад", "🏠 Главное меню")
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
        "Полный справочник по Terraria:\n"
        "• Боссы\n"
        "• NPC\n"
        "• Счастье и расселение\n\n"
        "Создан для новичков 👶",
        reply_markup=main_menu()
    )

# ================== BOSSES ==================

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"menu": "boss_stage"}
    await m.answer("Выбери этап:", reply_markup=stage_menu())

@dp.message_handler(lambda m: m.text == "🌱 До Хардмода")
async def bosses_pre(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer(
        "🌱 Боссы до Хардмода:",
        reply_markup=bosses_list("Дохардмод")
    )

@dp.message_handler(lambda m: m.text == "⚙️ Хардмод")
async def bosses_hard(m: types.Message):
    user_state[m.from_user.id]["menu"] = "boss_list"
    await m.answer(
        "⚙️ Боссы Хардмода:",
        reply_markup=bosses_list("Хардмод")
    )

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_select(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id]["boss"] = key
            await m.answer(
                f"{boss['name']}\n"
                f"Сложность: {boss['difficulty']}\n"
                f"Этап: {boss['stage']}",
                reply_markup=boss_sections()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "🛡 Подготовка", "🏗 Арена", "⚔ Оружие",
    "🧠 Тактика", "⚠ Опасности", "🎁 Зачем убивать"
])
async def boss_section(m: types.Message):
    uid = m.from_user.id
    boss = BOSSES[user_state[uid]["boss"]]
    mapping = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "⚠ Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }
    await m.answer(
        boss["sections"][mapping[m.text]],
        reply_markup=boss_sections()
    )

# ================== NPC ==================

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_menu(m: types.Message):
    user_state[m.from_user.id] = {"menu": "npc_stage"}
    await m.answer("Выбери этап NPC:", reply_markup=stage_menu())

@dp.message_handler(lambda m: m.text in ["🌱 До Хардмода", "⚙️ Хардмод"])
async def npc_stage(m: types.Message):
    stage = "Дохардмод" if "До" in m.text else "Хардмод"
    user_state[m.from_user.id]["menu"] = "npc_list"
    await m.answer(
        f"{stage} NPC:",
        reply_markup=npc_list(stage)
    )

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_select(m: types.Message):
    for key, npc in NPCS.items():
        if npc["name"] == m.text:
            user_state[m.from_user.id]["npc"] = key
            await m.answer(
                npc["name"],
                reply_markup=npc_sections()
            )
            return

@dp.message_handler(lambda m: m.text in [
    "📖 Описание", "🔓 Как получить", "🌍 Биом",
    "🏘️ Соседи", "😊 Счастье", "💡 Советы"
])
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["npc"]]
    mapping = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }
    await m.answer(
        npc["sections"][mapping[m.text]],
        reply_markup=npc_sections()
    )

# ================== NAV ==================

@dp.message_handler(lambda m: m.text in ["⬅ Назад", "🏠 Главное меню"])
async def back(m: types.Message):
    await start(m)

# ================== RUN ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)