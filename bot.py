import json
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ===== LOAD DATA =====
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)["npcs"]

with open("data/classes.json", encoding="utf-8") as f:
    CLASSES = json.load(f)

# ===== STATE =====
user_state = {}

# ===== KEYBOARDS =====

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("🎭 Классы")
    kb.add("📘 О боте")
    return kb

def stage_menu(mode):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if mode == "boss":
        kb.add("🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода")
    elif mode == "npc":
        kb.add("🌱 NPC до Хардмода", "⚙️ NPC Хардмода")
    kb.add("🏠 Главное меню")
    return kb

def list_menu(names):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for n in names:
        kb.add(n)
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

def boss_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

def npc_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

def class_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CLASSES.values():
        kb.add(c["name"])
    kb.add("🏠 Главное меню")
    return kb

def class_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🛡 Броня")
    kb.add("⚔ Оружие", "💍 Аксессуары")
    kb.add("🧪 Зелья", "📈 Прогресс")
    kb.add("❌ Ошибки")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

# ===== START =====

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state.pop(m.from_user.id, None)
    await m.answer("🎮 Terraria Guide Bot", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "Terraria Guide Bot\n\n"
        "Подробные гайды по:\n"
        "• Боссам\n"
        "• NPC\n"
        "• Классам\n\n"
        "Создан для новичков и хардкорщиков.",
        reply_markup=main_menu()
    )

# ===== BOSSES =====

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_root(m):
    user_state[m.from_user.id] = {"mode": "boss"}
    await m.answer("Выбери этап:", reply_markup=stage_menu("boss"))

@dp.message_handler(lambda m: m.text in ["🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода"])
async def bosses_stage(m):
    stage = "Дохардмод" if "до" in m.text else "Хардмод"
    uid = m.from_user.id
    user_state[uid].update({"stage": stage})
    bosses = [b["name"] for b in BOSSES.values() if b["stage"] == stage]
    await m.answer(f"{stage} — боссы:", reply_markup=list_menu(bosses))

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_selected(m):
    for k, b in BOSSES.items():
        if m.text == b["name"]:
            user_state[m.from_user.id]["item"] = k
            await m.answer(b["name"], reply_markup=boss_sections())

@dp.message_handler(lambda m: m.text in ["🛡 Подготовка","🏗 Арена","⚔ Оружие","🧠 Тактика","🔥 Опасности","🎁 Зачем убивать"])
async def boss_section(m):
    uid = m.from_user.id
    boss = BOSSES[user_state[uid]["item"]]
    mapping = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }
    await m.answer(boss["sections"][mapping[m.text]], reply_markup=boss_sections())

# ===== NPC =====

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_root(m):
    user_state[m.from_user.id] = {"mode": "npc"}
    await m.answer("Выбери этап:", reply_markup=stage_menu("npc"))

@dp.message_handler(lambda m: m.text in ["🌱 NPC до Хардмода", "⚙️ NPC Хардмода"])
async def npc_stage(m):
    stage = "Дохардмод" if "до" in m.text else "Хардмод"
    uid = m.from_user.id
    user_state[uid].update({"stage": stage})
    npcs = [n["name"] for n in NPCS.values() if n.get("stage") == stage]
    await m.answer(f"{stage} — NPC:", reply_markup=list_menu(npcs))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_selected(m):
    for k, n in NPCS.items():
        if m.text == n["name"]:
            user_state[m.from_user.id]["item"] = k
            await m.answer(n["name"], reply_markup=npc_sections())

@dp.message_handler(lambda m: m.text in ["📖 Описание","🔓 Как получить","🌍 Биом","🏘️ Соседи","😊 Счастье","💡 Советы"])
async def npc_section(m):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["item"]]
    mapping = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }
    await m.answer(npc["sections"][mapping[m.text]], reply_markup=npc_sections())

# ===== CLASSES =====

@dp.message_handler(lambda m: m.text == "🎭 Классы")
async def classes_root(m):
    user_state[m.from_user.id] = {"mode": "class"}
    await m.answer("Выбери класс:", reply_markup=class_menu())

@dp.message_handler(lambda m: m.text in [c["name"] for c in CLASSES.values()])
async def class_selected(m):
    for k, c in CLASSES.items():
        if m.text == c["name"]:
            user_state[m.from_user.id]["item"] = k
            await m.answer(c["name"], reply_markup=class_sections())

@dp.message_handler(lambda m: m.text in ["📖 Описание","🛡 Броня","⚔ Оружие","💍 Аксессуары","🧪 Зелья","📈 Прогресс","❌ Ошибки"])
async def class_section(m):
    uid = m.from_user.id
    cls = CLASSES[user_state[uid]["item"]]
    mapping = {
        "📖 Описание": "description",
        "🛡 Броня": "armor",
        "⚔ Оружие": "weapons",
        "💍 Аксессуары": "accessories",
        "🧪 Зелья": "potions",
        "📈 Прогресс": "progression",
        "❌ Ошибки": "mistakes"
    }
    await m.answer(cls["sections"][mapping[m.text]], reply_markup=class_sections())

# ===== BACK =====

@dp.message_handler(lambda m: m.text == "⬅ Назад")
async def back(m):
    await start(m)

# ===== RUN =====

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)