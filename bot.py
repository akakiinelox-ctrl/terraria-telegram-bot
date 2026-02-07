import json
from aiogram import Bot, Dispatcher, executor, types

# ================== TOKEN ==================
API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================== LOAD DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)["npcs"]

# ================== HELPERS ==================

def normalize_stage(stage: str) -> str:
    s = stage.lower().strip()

    if s in ["дохардмод", "до хардмода"]:
        return "pre"

    if "переход" in s:
        return "hard"

    if s == "хардмод":
        return "hard"

    return "pre"

# ================== STATE ==================
user_state = {}
# {
#   user_id: {
#       mode: boss | npc
#       stage: pre | hard
#       item: id
#   }
# }

# ================== KEYBOARDS ==================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def stage_menu(mode):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 До Хардмода", "⚙️ Хардмод")
    kb.add("🏠 Главное меню")
    return kb

def list_menu(items):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in items:
        kb.add(name)
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def boss_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def npc_sections():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

# ================== NAVIGATION ==================

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def go_main(m: types.Message):
    user_state.pop(m.from_user.id, None)
    await start(m)

@dp.message_handler(lambda m: m.text == "⬅ К списку")
async def go_list(m: types.Message):
    uid = m.from_user.id
    state = user_state.get(uid)

    if not state:
        await start(m)
        return

    if state["mode"] == "boss":
        items = [
            b["name"] for b in BOSSES.values()
            if normalize_stage(b["stage"]) == state["stage"]
        ]
        await m.answer("Боссы:", reply_markup=list_menu(items))

    else:
        items = [
            n["name"] for n in NPCS.values()
            if normalize_stage(n["stage"]) == state["stage"]
        ]
        await m.answer("NPC:", reply_markup=list_menu(items))

# ================== START ==================

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбери раздел 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "Полный справочник по боссам и NPC Terraria.\n"
        "Корректный прогресс, подробные гайды.",
        reply_markup=main_menu()
    )

# ================== BOSSES ==================

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_root(m: types.Message):
    user_state[m.from_user.id] = {"mode": "boss"}
    await m.answer("Выбери этап:", reply_markup=stage_menu("boss"))

@dp.message_handler(lambda m: m.text in ["🌱 До Хардмода", "⚙️ Хардмод"])
async def bosses_stage(m: types.Message):
    stage = "pre" if "До" in m.text else "hard"
    uid = m.from_user.id
    user_state[uid]["stage"] = stage

    items = [
        b["name"] for b in BOSSES.values()
        if normalize_stage(b["stage"]) == stage
    ]

    await m.answer("Боссы:", reply_markup=list_menu(items))

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_selected(m: types.Message):
    for k, b in BOSSES.items():
        if m.text == b["name"]:
            user_state[m.from_user.id]["item"] = k
            await m.answer(
                f"{b['name']}\nСложность: {b['difficulty']}",
                reply_markup=boss_sections()
            )

@dp.message_handler(lambda m: m.text in [
    "🛡 Подготовка", "🏗 Арена", "⚔ Оружие",
    "🧠 Тактика", "🔥 Опасности", "🎁 Зачем убивать"
])
async def boss_section(m: types.Message):
    uid = m.from_user.id
    boss = BOSSES[user_state[uid]["item"]]

    key_map = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }

    await m.answer(
        boss["sections"][key_map[m.text]],
        reply_markup=boss_sections()
    )

# ================== NPC ==================

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_root(m: types.Message):
    user_state[m.from_user.id] = {"mode": "npc"}
    await m.answer("Выбери этап:", reply_markup=stage_menu("npc"))

@dp.message_handler(lambda m: m.text in ["🌱 До Хардмода", "⚙️ Хардмод"])
async def npc_stage(m: types.Message):
    stage = "pre" if "До" in m.text else "hard"
    uid = m.from_user.id
    user_state[uid]["stage"] = stage

    items = [
        n["name"] for n in NPCS.values()
        if normalize_stage(n["stage"]) == stage
    ]

    await m.answer("NPC:", reply_markup=list_menu(items))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_selected(m: types.Message):
    for k, n in NPCS.items():
        if m.text == n["name"]:
            user_state[m.from_user.id]["item"] = k
            await m.answer(n["name"], reply_markup=npc_sections())

@dp.message_handler(lambda m: m.text in [
    "📖 Описание", "🔓 Как получить", "🌍 Биом",
    "🏘️ Соседи", "😊 Счастье", "💡 Советы"
])
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["item"]]

    key_map = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }

    await m.answer(
        npc["sections"][key_map[m.text]],
        reply_markup=npc_sections()
    )

# ================== RUN ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)