import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "TOKEN_TYT"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- ЗАГРУЗКА ДАННЫХ ----------
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

PROGRESS_FILE = "data/users_progress.json"
FAVORITES_FILE = "data/favorites.json"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- КЛАВИАТУРЫ ----------
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("⭐ Избранное", "📊 Прогресс")
    return kb

def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, boss in BOSSES.items():
        kb.add(boss["icon"] + " " + boss["name"])
    kb.add("🏠 Главное меню")
    return kb

def boss_actions_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Пройден", "⭐ В избранное")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

# ---------- START ----------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nИспользуй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ---------- ГЛАВНОЕ МЕНЮ ----------
@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

# ---------- БОССЫ ----------
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer("👁 Выбери босса:", reply_markup=bosses_kb())

# ---------- ГАЙД ПО БОССУ ----------
@dp.message_handler(lambda m: any(m.text.endswith(b["name"]) for b in BOSSES.values()))
async def boss_guide(message: types.Message):
    boss = next(b for b in BOSSES.values() if message.text.endswith(b["name"]))

    text = (
        f"{boss['icon']} *{boss['name']}*\n"
        f"🔘 Сложность: {boss['difficulty']}\n\n"
        f"⚠️ *Опасность:*\n{boss['threat_profile']}\n\n"
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

    await message.answer(text, reply_markup=boss_actions_kb(), parse_mode="Markdown")

# ---------- ПРОЙДЕН ----------
@dp.message_handler(lambda m: m.text == "✅ Пройден")
async def mark_completed(message: types.Message):
    user_id = str(message.from_user.id)
    progress = load_json(PROGRESS_FILE)

    progress.setdefault(user_id, []).append("✔ Босс побеждён")
    progress[user_id] = list(set(progress[user_id]))

    save_json(PROGRESS_FILE, progress)
    await message.answer("✅ Отмечено как пройдено!")

# ---------- ИЗБРАННОЕ ----------
@dp.message_handler(lambda m: m.text == "⭐ В избранное")
async def add_favorite(message: types.Message):
    user_id = str(message.from_user.id)
    favs = load_json(FAVORITES_FILE)

    favs.setdefault(user_id, []).append("⭐ Босс")
    favs[user_id] = list(set(favs[user_id]))

    save_json(FAVORITES_FILE, favs)
    await message.answer("⭐ Добавлено в избранное!")

# ---------- ПРОГРЕСС ----------
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(message: types.Message):
    user_id = str(message.from_user.id)
    progress = load_json(PROGRESS_FILE)

    completed = progress.get(user_id, [])
    percent = int(len(completed) / len(BOSSES) * 100) if BOSSES else 0

    text = f"📊 Прогресс: {percent}%\n\n" + "\n".join(completed or ["— пока пусто —"])
    await message.answer(text)

# ---------- ИЗБРАННОЕ ----------
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    user_id = str(message.from_user.id)
    favs = load_json(FAVORITES_FILE)

    text = "⭐ Избранное:\n\n" + "\n".join(favs.get(user_id, ["— пусто —"]))
    await message.answer(text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)