import json
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD DATA ----------

with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

with open("data/npcs.json", encoding="utf-8") as f:
    NPC_DATA = json.load(f)
    NPCS = NPC_DATA["npcs"]

# ---------- STATE ----------
# user_id -> {"mode": "boss" | "npc", "npc": key, "boss": key}
user_state = {}

# ---------- KEYBOARDS ----------

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb


# ===== NPC =====

def npc_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 До Хардмода", "⚙️ Хардмод")
    kb.add("⬅ Назад")
    return kb


def npc_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for npc in NPCS.values():
        if npc.get("stage") == stage:
            kb.add(npc["name"])
    kb.add("⬅ Назад")
    return kb


def npc_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ С кем селить")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ К списку NPC", "🏠 Главное меню")
    return kb


# ===== BOSSES =====
# (мы НЕ меняем твою логику, только минимально подключаем меню)

def bosses_stage_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌱 Начало приключения", "⚙️ Хардмод")
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
        "Подробные гайды по боссам и NPC Terraria.\n"
        "Счастье, биомы, тактики и прогресс.",
        reply_markup=main_menu()
    )

# ===== NPC FLOW =====

@dp.message_handler(lambda m: "NPC" in m.text)
async def npc_entry(m: types.Message):
    user_state[m.from_user.id] = {"mode": "npc"}
    await m.answer("🧑 NPC Terraria — выбери этап:", reply_markup=npc_stage_menu())


@dp.message_handler(lambda m: "До Хардмода" in m.text)
async def npc_pre(m: types.Message):
    await m.answer("🌱 NPC до Хардмода:", reply_markup=npc_list("prehardmode"))


@dp.message_handler(lambda m: "Хардмод" in m.text)
async def npc_hard(m: types.Message):
    await m.answer("⚙️ NPC Хардмода:", reply_markup=npc_list("hardmode"))


@dp.message_handler(lambda m: m.text in [n["name"] for n in NPCS.values()])
async def npc_select(m: types.Message):
    for key, npc in NPCS.items():
        if m.text == npc["name"]:
            user_state[m.from_user.id] = {"mode": "npc", "npc": key}
            await m.answer(npc["name"], reply_markup=npc_menu())
            return


@dp.message_handler(lambda m: any(x in m.text for x in [
    "Описание", "Как получить", "Биом",
    "С кем", "Счастье", "Советы"
]))
async def npc_section(m: types.Message):
    uid = m.from_user.id
    npc = NPCS[user_state[uid]["npc"]]

    section_map = {
        "Описание": "description",
        "Как получить": "how_to_get",
        "Биом": "biome",
        "С кем": "neighbors",
        "Счастье": "happiness",
        "Советы": "tips"
    }

    for key in section_map:
        if key in m.text:
            await m.answer(
                npc["sections"][section_map[key]],
                reply_markup=npc_menu()
            )
            return


@dp.message_handler(lambda m: "К списку NPC" in m.text)
async def back_to_npc_list(m: types.Message):
    await npc_entry(m)

# ===== BOSSES FLOW (БАЗОВО, БЕЗ ЛОМКИ) =====

@dp.message_handler(lambda m: "Боссы" in m.text)
async def bosses_entry(m: types.Message):
    await m.answer("Выбери этап:", reply_markup=bosses_stage_menu())


@dp.message_handler(lambda m: "Начало приключения" in m.text)
async def bosses_pre(m: types.Message):
    await m.answer("🌱 Боссы начала игры:", reply_markup=bosses_list("Дохардмод"))


@dp.message_handler(lambda m: "Хардмод" in m.text and user_state.get(m.from_user.id, {}).get("mode") != "npc")
async def bosses_hard(m: types.Message):
    await m.answer("⚙️ Боссы Хардмода:", reply_markup=bosses_list("Хардмод"))


@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def boss_select(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id] = {"mode": "boss", "boss": key}
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


# ===== BACK =====

@dp.message_handler(lambda m: "Назад" in m.text or "Главное" in m.text)
async def back(m: types.Message):
    await start(m)


# ---------- RUN ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)