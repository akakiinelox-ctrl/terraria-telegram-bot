# bot/bot.py
import json
import os
from aiogram import Bot, Dispatcher, executor, types

# ====== CONFIG: токен ======
# Рекомендуется задавать через переменную окружения BOT_TOKEN.
# Если хочешь — можешь прямо прописать токен в переменной ниже.
API_TOKEN = os.getenv("BOT_TOKEN", "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ====== УТИЛИТЫ: загрузка JSON с гибкостью формата ======
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

raw_bosses = load_json("data/bosses.json")
raw_npcs = load_json("data/npcs.json")

if raw_bosses is None:
    print("ERROR: data/bosses.json not found or unreadable.")
    BOSSES = {}
else:
    # ожидание: raw_bosses is a dict mapping id->object
    BOSSES = raw_bosses

if raw_npcs is None:
    print("ERROR: data/npcs.json not found or unreadable.")
    NPCS = {}
else:
    # поддержка двух форматов: { "npcs": {...} } или сразу {...}
    if isinstance(raw_npcs, dict) and "npcs" in raw_npcs and isinstance(raw_npcs["npcs"], dict):
        NPCS = raw_npcs["npcs"]
    else:
        NPCS = raw_npcs

# ====== State (in-memory) ======
user_state = {}
# структура:
# user_state[user_id] = {"mode": "boss"|"npc", "stage": "Дохардмод"|"Хардмод", "item": "id"}

# ====== Keyboard builders ======
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы", "🧑 NPC")
    kb.add("📘 О боте")
    return kb

def stage_menu_kb(mode):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if mode == "boss":
        kb.add("🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода")
    else:
        kb.add("🌱 NPC до Хардмода", "⚙️ NPC Хардмода")
    kb.add("🏠 Главное меню")
    return kb

def list_menu_kb(names):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for n in names:
        kb.add(n)
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def boss_sections_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛡 Подготовка", "🏗 Арена")
    kb.add("⚔ Оружие", "🧠 Тактика")
    kb.add("🔥 Опасности", "🎁 Зачем убивать")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

def npc_sections_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📖 Описание", "🔓 Как получить")
    kb.add("🌍 Биом", "🏘️ Соседи")
    kb.add("😊 Счастье", "💡 Советы")
    kb.add("⬅ К списку", "🏠 Главное меню")
    return kb

# ====== Помощники ======
def build_name_to_id_map(items_dict):
    # items_dict: id -> { "name": "..." , ... }
    name_to_id = {}
    for k, v in items_dict.items():
        name = v.get("name")
        if name:
            name_to_id[name] = k
    return name_to_id

BOSS_NAME_TO_ID = build_name_to_id_map(BOSSES)
NPC_NAME_TO_ID = build_name_to_id_map(NPCS)

def is_hardmode_stage(item_stage):
    # если в строке есть "хард" — относим к хардмоду
    if not item_stage:
        return False
    return "хард" in item_stage.lower()

# ====== NAVIGATION handlers (всегда первыми) ======

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def handler_home(m: types.Message):
    user_state.pop(m.from_user.id, None)
    await start_cmd(m)

@dp.message_handler(lambda m: m.text == "⬅ К списку")
async def handler_back_to_list(m: types.Message):
    uid = m.from_user.id
    st = user_state.get(uid)
    if not st:
        await start_cmd(m)
        return

    mode = st.get("mode")
    stage = st.get("stage")

    if mode == "boss":
        # выберем все боссы, чей stage соответствует выбору (хард/не хард)
        target_hard = (stage == "Хардмод")
        bosses = [b.get("name") for b in BOSSES.values() if bool(is_hardmode_stage(b.get("stage", ""))) == target_hard]
        await m.answer(f"{stage} — боссы:", reply_markup=list_menu_kb(bosses))
        return

    if mode == "npc":
        target_hard = (stage == "Хардмод")
        npcs = [n.get("name") for n in NPCS.values() if bool(is_hardmode_stage(n.get("stage", ""))) == target_hard]
        await m.answer(f"{stage} — NPC:", reply_markup=list_menu_kb(npcs))
        return

    await start_cmd(m)

# ====== START / ABOUT ======
@dp.message_handler(commands=["start"])
async def start_cmd(m: types.Message):
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбирай раздел 👇",
        reply_markup=main_menu_kb()
    )

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def handler_about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\nПолные гайды по боссам и NPC Terraria.\nСоздан для удобного справочника и быстрого поиска информации.",
        reply_markup=main_menu_kb()
    )

# ====== BOSSES flow ======
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def handler_bosses_root(m: types.Message):
    user_state[m.from_user.id] = {"mode": "boss"}
    await m.answer("Выбери этап:", reply_markup=stage_menu_kb("boss"))

@dp.message_handler(lambda m: m.text in ["🌱 Боссы до Хардмода", "⚙️ Боссы Хардмода"])
async def handler_bosses_stage(m: types.Message):
    uid = m.from_user.id
    if uid not in user_state:
        user_state[uid] = {"mode": "boss"}

    stage = "Дохардмод" if "до" in m.text.lower() else "Хардмод"
    user_state[uid].update({"stage": stage})

    target_hard = (stage == "Хардмод")
    names = [b.get("name") for b in BOSSES.values() if bool(is_hardmode_stage(b.get("stage", ""))) == target_hard]
    if not names:
        await m.answer("Список пуст — проверь файл data/bosses.json", reply_markup=stage_menu_kb("boss"))
        return
    await m.answer(f"{stage} — боссы:", reply_markup=list_menu_kb(names))

@dp.message_handler(lambda m: m.text in BOSS_NAME_TO_ID.keys())
async def handler_boss_select(m: types.Message):
    uid = m.from_user.id
    boss_id = BOSS_NAME_TO_ID.get(m.text)
    if not boss_id:
        return
    user_state.setdefault(uid, {})["item"] = boss_id
    boss = BOSSES[boss_id]
    await m.answer(f"{boss.get('name')}\n\nСложность: {boss.get('difficulty','?')}\nЭтап: {boss.get('stage','?')}",
                   reply_markup=boss_sections_kb())

@dp.message_handler(lambda m: m.text in ["🛡 Подготовка", "🏗 Арена", "⚔ Оружие", "🧠 Тактика", "🔥 Опасности", "🎁 Зачем убивать"])
async def handler_boss_section(m: types.Message):
    uid = m.from_user.id
    st = user_state.get(uid)
    if not st or "item" not in st:
        await m.answer("Сначала выбери босса.", reply_markup=main_menu_kb())
        return
    boss = BOSSES.get(st["item"])
    mapping = {
        "🛡 Подготовка": "preparation",
        "🏗 Арена": "arena",
        "⚔ Оружие": "weapons",
        "🧠 Тактика": "tactics",
        "🔥 Опасности": "dangers",
        "🎁 Зачем убивать": "why_kill"
    }
    key = mapping.get(m.text)
    text = boss.get("sections", {}).get(key, "Информация отсутствует.")
    await m.answer(text, reply_markup=boss_sections_kb())

# ====== NPC flow ======
@dp.message_handler(lambda m: m.text == "🧑 NPC")
async def handler_npc_root(m: types.Message):
    user_state[m.from_user.id] = {"mode": "npc"}
    await m.answer("Выбери этап:", reply_markup=stage_menu_kb("npc"))

@dp.message_handler(lambda m: m.text in ["🌱 NPC до Хардмода", "⚙️ NPC Хардмода"])
async def handler_npc_stage(m: types.Message):
    uid = m.from_user.id
    if uid not in user_state:
        user_state[uid] = {"mode": "npc"}

    stage = "Дохардмод" if "до" in m.text.lower() else "Хардмод"
    user_state[uid].update({"stage": stage})

    target_hard = (stage == "Хардмод")
    names = [n.get("name") for n in NPCS.values() if bool(is_hardmode_stage(n.get("stage", ""))) == target_hard]
    if not names:
        await m.answer("Список пуст — проверь файл data/npcs.json", reply_markup=stage_menu_kb("npc"))
        return
    await m.answer(f"{stage} — NPC:", reply_markup=list_menu_kb(names))

@dp.message_handler(lambda m: m.text in NPC_NAME_TO_ID.keys())
async def handler_npc_select(m: types.Message):
    uid = m.from_user.id
    npc_id = NPC_NAME_TO_ID.get(m.text)
    if not npc_id:
        return
    user_state.setdefault(uid, {})["item"] = npc_id
    npc = NPCS[npc_id]
    await m.answer(f"{npc.get('name')}", reply_markup=npc_sections_kb())

@dp.message_handler(lambda m: m.text in ["📖 Описание", "🔓 Как получить", "🌍 Биом", "🏘️ Соседи", "😊 Счастье", "💡 Советы"])
async def handler_npc_section(m: types.Message):
    uid = m.from_user.id
    st = user_state.get(uid)
    if not st or "item" not in st:
        await m.answer("Сначала выбери NPC.", reply_markup=main_menu_kb())
        return
    npc = NPCS.get(st["item"])
    mapping = {
        "📖 Описание": "description",
        "🔓 Как получить": "how_to_get",
        "🌍 Биом": "biome",
        "🏘️ Соседи": "neighbors",
        "😊 Счастье": "happiness",
        "💡 Советы": "tips"
    }
    key = mapping.get(m.text)
    text = npc.get("sections", {}).get(key, "Информация отсутствует.")
    await m.answer(text, reply_markup=npc_sections_kb())

# ====== Fallback minimal handler (логирование для дебага) ======
@dp.message_handler()
async def handler_fallback(m: types.Message):
    # небольшой дружественный ответ, чтобы не было "тишины"
    # избегаем перехвата навигационных команд (они выше)
    await m.answer("Не понял команду. Используй меню.", reply_markup=main_menu_kb())

# ====== RUN ======
if __name__ == "__main__":
    print("Bot starting... make sure BOT_TOKEN is set or hard-coded above.")
    executor.start_polling(dp, skip_updates=True)