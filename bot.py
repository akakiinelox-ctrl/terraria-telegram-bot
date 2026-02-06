import json
from aiogram import Bot, Dispatcher, executor, types
from keyboards import main_menu_kb, bosses_kb, boss_actions_kb

BOT_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD ----------
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- STATE ----------
user_current_boss = {}

# ---------- START ----------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nВыбери действие:",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ---------- MAIN MENU ----------
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 Выбери босса:",
        reply_markup=bosses_kb(BOSSES)
    )

# ---------- BOSS GUIDE ----------
@dp.message_handler(lambda m: any(m.text.endswith(b["name"]) for b in BOSSES.values()))
async def boss_guide(message: types.Message):
    boss_key = next(k for k, v in BOSSES.items() if message.text.endswith(v["name"]))
    boss = BOSSES[boss_key]
    user_current_boss[message.from_user.id] = boss_key

    text = (
        f"{boss['icon']} *{boss['name']}*\n\n"
        f"⚔ Сложность: {boss['difficulty']}\n\n"
        f"🎯 *Угроза:*\n{boss['threat_profile']}\n\n"
        f"🛡 *Броня:*\n{boss['recommended_armor']}\n\n"
        f"⚔ *Оружие:*\n"
        f"• Воин: {boss['weapons']['warrior']}\n"
        f"• Стрелок: {boss['weapons']['ranger']}\n"
        f"• Маг: {boss['weapons']['mage']}\n"
        f"• Призыватель: {boss['weapons']['summoner']}\n\n"
        f"🏗 *Арена:*\n{boss['arena_blueprint']}\n\n"
        f"🧠 *Тактика:*\n{boss['boss_behavior']}\n\n"
        f"🎁 *Зачем убивать:*\n{boss['progression_value']}"
    )

    await message.answer(
        text,
        reply_markup=boss_actions_kb(),
        parse_mode="Markdown"
    )

# ---------- FAVORITES ----------
@dp.message_handler(lambda m: m.text == "⭐ В избранное")
async def add_favorite(message: types.Message):
    uid = str(message.from_user.id)
    boss = user_current_boss.get(message.from_user.id)

    if not boss:
        return

    favs = load_json("data/favorites.json")
    favs.setdefault(uid, [])

    if boss not in favs[uid]:
        favs[uid].append(boss)
        save_json("data/favorites.json", favs)

    await message.answer("⭐ Добавлено в избранное")

@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    uid = str(message.from_user.id)
    favs = load_json("data/favorites.json").get(uid, [])

    if not favs:
        await message.answer("⭐ Избранное пусто")
        return

    text = "⭐ *Избранное:*\n\n" + "\n".join(
        f"{BOSSES[b]['icon']} {BOSSES[b]['name']}" for b in favs
    )

    await message.answer(text, parse_mode="Markdown")

# ---------- PROGRESS ----------
@dp.message_handler(lambda m: m.text == "✅ Пройден")
async def mark_done(message: types.Message):
    uid = str(message.from_user.id)
    boss = user_current_boss.get(message.from_user.id)

    if not boss:
        return

    progress = load_json("data/users_progress.json")
    progress.setdefault(uid, [])

    if boss not in progress[uid]:
        progress[uid].append(boss)
        save_json("data/users_progress.json", progress)

    await message.answer("✅ Отмечено как пройдено")

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(message: types.Message):
    uid = str(message.from_user.id)
    done = load_json("data/users_progress.json").get(uid, [])

    total = len(BOSSES)
    completed = len(done)

    text = f"📊 *Прогресс:*\n\nПройдено: {completed} / {total}"

    await message.answer(text, parse_mode="Markdown")

# ---------- NAV ----------
@dp.message_handler(lambda m: m.text in ["⬅ Назад", "🏠 Главное меню"])
async def back(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)