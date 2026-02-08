import json
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================= LOAD DATA =================

with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPCS = json.load(f)

# ================= STATE =================
# level:
# main -> stage -> list -> item -> section

user_state = {}

def set_state(uid, **kwargs):
    user_state.setdefault(uid, {})
    user_state[uid].update(kwargs)

def get_state(uid):
    return user_state.get(uid, {})

# ================= HELPERS =================

def normalize_stage(stage: str):
    s = stage.lower()
    if "хард" in s and "до" not in s:
        return "hard"
    return "pre"

def filter_by_stage(data, stage):
    return {
        k: v for k, v in data.items()
        if normalize_stage(v.get("stage", "")) == stage
    }

# ================= KEYBOARDS =================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def stage_menu(mode):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if mode == "boss":
        kb.add("🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода")
    else:
        kb.add("🌱 NPC до Хардмода", "⚙️ NPC Хардмода")
    kb.add("🏠 Главное меню")
    return kb

def list_menu(items):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in items:
        kb.add(i)
    kb.add("⬅ К этапам", "🏠 Главное меню")
    return kb

def section_menu(mode):
    if mode == "boss":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🛡 Подготовка", "🏗 Арена")
        kb.add("⚔ Оружие", "🧠 Тактика")
        kb.add("🔥 Опасности", "🎁 Зачем убивать")
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📖 Описание", "🔓 Как получить")
        kb.add("🌍 Биом", "🏘️ Соседи")
        kb.add("😊 Счастье", "💡 Советы")

    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

# ================= NAVIGATION =================

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user_state.pop(m.from_user.id, None)
    await m.answer("🎮 Terraria Guide Bot\n\nВыбери раздел 👇", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def back_main(m: types.Message):
    await start(m)

@dp.message_handler(lambda m: m.text == "⬅ К этапам")
async def back_to_stage(m: types.Message):
    st = get_state(m.from_user.id)
    await m.answer("Выбери этап:", reply_markup=stage_menu(st["mode"]))

@dp.message_handler(lambda m: m.text == "⬅ К списку")
async def back_to_list(m: types.Message):
    st = get_state(m.from_user.id)
    data = BOSSES if st["mode"] == "boss" else NPCS
    items = filter_by_stage(data, st["stage"])
    await m.answer(
        "Выбери:",
        reply_markup=list_menu([v["name"] for v in items.values()])
    )

# ================= BOSSES =================

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_root(m: types.Message):
    set_state(m.from_user.id, mode="boss")
    await m.answer("Выбери этап:", reply_markup=stage_menu("boss"))

@dp.message_handler(lambda m: m.text in ["🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода"])
async def bosses_stage(m: types.Message):
    stage = "pre" if "до" in m.text else "hard"
    set_state(m.from_user.id, stage=stage)
    items = filter_by_stage(BOSSES, stage)
    await m.answer("Боссы:", reply_markup=list_menu([v["name"] for v in items.values()]))

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_selected(m: types.Message):
    for k, v in BOSSES.items():
        if v["name"] == m.text:
            set_state(m.from_user.id, item=k)
            await m.answer(v["name"], reply_markup=section_menu("boss"))
            return

@dp.message_handler(lambda m: m.text in ["🛡 Подготовка","🏗 Арена","⚔ Оружие","🧠 Тактика","🔥 Опасности","🎁 Зачем убивать"])
async def boss_section(m: types.Message):
    st = get_state(m.from_user.id)
    sec = {
        "🛡 Подготовка":"preparation",
        "🏗 Арена":"arena",
        "⚔ Оружие":"weapons",
        "🧠 Тактика":"tactics",
        "🔥 Опасности":"dangers",
        "🎁 Зачем убивать":"why_kill"
    }
    await m.answer(
        BOSSES[st["item"]]["sections"][sec[m.text]],
        reply_markup=section_menu("boss")
    )

# ================= NPC =================

@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def npc_root(m: types.Message):
    set_state(m.from_user.id, mode="npc")
    await m.answer("Выбери этап:", reply_markup=stage_menu("npc"))

@dp.message_handler(lambda m: m.text in ["🌱 NPC до Хардмода", "⚙️ NPC Хардмода"])
async def npc_stage(m: types.Message):
    stage = "pre" if "до" in m.text else "hard"
    set_state(m.from_user.id, stage=stage)
    items = filter_by_stage(NPCS, stage)
    await m.answer("NPC:", reply_markup=list_menu([v["name"] for v in items.values()]))

@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_selected(m: types.Message):
    for k, v in NPCS.items():
        if v["name"] == m.text:
            set_state(m.from_user.id, item=k)
            await m.answer(v["name"], reply_markup=section_menu("npc"))
            return

@dp.message_handler(lambda m: m.text in ["📖 Описание","🔓 Как получить","🌍 Биом","🏘️ Соседи","😊 Счастье","💡 Советы"])
async def npc_section(m: types.Message):
    st = get_state(m.from_user.id)
    sec = {
        "📖 Описание":"description",
        "🔓 Как получить":"how_to_get",
        "🌍 Биом":"biome",
        "🏘️ Соседи":"neighbors",
        "😊 Счастье":"happiness",
        "💡 Советы":"tips"
    }
    await m.answer(
        NPCS[st["item"]]["sections"][sec[m.text]],
        reply_markup=section_menu("npc")
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)