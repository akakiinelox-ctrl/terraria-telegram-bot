import json
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD DATA ----------
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

# ---------- STATE ----------
user_state = {}  # user_id -> {"menu": str, "boss": str}

# ---------- KEYBOARDS ----------

def main_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "👁 Боссы",
        "📘 О боте"
    )

def bosses_stage_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "🌱 Начало приключения",
        "⬅ Назад"
    )

def bosses_list(stage):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, boss in BOSSES.items():
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
    user_state[m.from_user.id] = {"menu": "main"}
    await m.answer(
        "🎮 Terraria Guide Bot\n\nВыбери раздел 👇",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "📘 О боте")
async def about(m: types.Message):
    await m.answer(
        "📘 Terraria Guide Bot\n\n"
        "Полноценный справочник по боссам Terraria.\n"
        "Создан для новичков.",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses(m: types.Message):
    user_state[m.from_user.id] = {"menu": "stages"}
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

@dp.message_handler(lambda m: m.text in [b["name"] for b in BOSSES.values()])
async def select_boss(m: types.Message):
    for key, boss in BOSSES.items():
        if m.text == boss["name"]:
            user_state[m.from_user.id]["boss"] = key
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

    key = section_map[m.text]
    await m.answer(
        boss["sections"][key],
        reply_markup=boss_menu()
    )

@dp.message_handler(lambda m: m.text == "⬅ К списку боссов")
async def back_to_bosses(m: types.Message):
    await pre_hardmode(m)

@dp.message_handler(lambda m: m.text == "🏠 Главное меню" or m.text == "⬅ Назад")
async def back(m: types.Message):
    await start(m)

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)