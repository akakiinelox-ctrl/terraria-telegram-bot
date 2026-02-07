import json
from aiogram import Bot, Dispatcher, executor, types

# ================== НАСТРОЙКИ ==================
API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================== ЗАГРУЗКА ДАННЫХ ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS_DATA = json.load(f)["npcs"]

# ================== СОСТОЯНИЕ ==================
user_state = {}  
# user_id -> {
#   "mode": "boss" | "npc",
#   "stage": str,
#   "boss": str,
#   "npc": str
# }

# ================== КНОПКИ ==================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def stage_menu():
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

def boss_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def npc_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 NPC до Хардмода")
    kb.add("⚙️ NPC Хардмода")
    kb.add("⬅ Назад")
    return kb

def npc_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, npc in NPCS_DATA.items():
        if npc.get("stage", "До Хардмода") == stage:
            kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb

def npc_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

# ================== ОБЩИЕ ==================

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
        "Создан для новичков и прохождения без ошибок.",
        reply_markup=main_menu()
    )

# ================== БОССЫ ==================

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"mode": "boss"}
    await m.answer("Выбери этап:", reply_markup=stage_menu())

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
    uid = m.from_user.id
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[uid]["boss"] = key
            await m.answer(
                f"{boss['name']}\n\n"
                f"Сложность: {boss['difficulty']}\n"
                f"Этап: {boss['stage']}",
                reply_markup=boss_sections()
            )

@dp.message_handler(lambda m: m.text in ["🛡 Подготовка","🏗 Арена","⚔ Оружие","🧠 Тактика","🔥 Опасности","🎁 Зачем убивать"])
async def boss_section(m: types.Message):
    uid = m.from_user.id
    boss = BOSSES[user_state[uid]["boss"]]
    mapping = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }
    await m.answer(boss["sections"][mapping[m.text]], reply_markup=boss_sections())

# ================== NPC ==================

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_main(m: types.Message):
    user_state[m.from_user.id] = {"mode": "npc"}
    await m.answer("NPC Terraria:", reply_markup=npc_stage_menu())

@dp.message_handler(lambda m: m.text == "🌱 NPC до Хардмода")
async def npc_pre(m: types.Message):
    await m.answer("NPC до Хардмода:", reply_markup=npc_list("До Хардмода"))

@dp.message_handler(lambda m: m.text == "⚙️ NPC Хардмода")
async def npc_hard(m: types.Message):
    await m.answer("NPC Хардмода:", reply_markup=npc_list("Хардмод"))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS_DATA.values()])
async def npc_select(m: types.Message):
    uid = m.from_user.id
    for key, npc in NPCS_DATA.items():
        if m.text == npc["name"]:
            user_state[uid]["npc"] = key
            await m.answer(npc["name"], reply_markup=npc_sections())

@dp.message_handler(lambda m: m.text in ["📖 Описание","🔓 Как получить","🌍 Биом","🏘️ Соседи","😊 Счастье","💡 Советы"])
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS_DATA[user_state[uid]["npc"]]
    map_sec = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }
    await m.answer(npc["sections"][map_sec[m.text]], reply_markup=npc_sections())

# ================== НАЗАД ==================

@dp.message_handler(lambda m: m.text in ["⬅ Назад","⬅ К списку","🏠 Главное меню"])
async def back(m: types.Message):
    await start(m)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)