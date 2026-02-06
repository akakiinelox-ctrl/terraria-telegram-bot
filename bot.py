import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "TOKEN_TUT"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- LOAD DATA ----------
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS_PROGRESS_PATH = "data/users_progress.json"
FAVORITES_PATH = "data/favorites.json"

user_current_boss = {}  # user_id -> boss_key

# ---------- KEYBOARDS ----------
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("⭐ Избранное", "📊 Прогресс")
    return kb

def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, boss in BOSSES.items():
        kb.add(f"{boss['icon']} {boss['name']}")
    kb.add("⬅ Назад")
    return kb

def boss_actions_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⭐ В избранное", "✅ Пройден")
    kb.add("⬅ Назад", "🏠 Главное меню")
    return kb

# ---------- START ----------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nВыбирай босса и получай подробный гайд.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ---------- MAIN MENU ----------
@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

# ---------- BOSSES ----------
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer("👁 Выбери босса:", reply_markup=bosses_kb())

# ---------- BOSS GUIDE ----------
@dp.message_handler(lambda m: any(m.text.endswith(b["name"]) for b in BOSSES.values()))
async def boss_guide(message: types.Message):
    boss_key = next(k for k, b in BOSSES.items() if message.text.endswith(b["name"]))
    boss = BOSSES[boss_key]

    user_current_boss[message.from_user.id] = boss_key

    text = (
        f"{boss['icon']} *{boss['name']}*\n"
        f"⚔ Сложность: *{boss['difficulty']}*\n\n"
        f"🧠 *Опасность:*\n{boss['threat_profile']}\n\n"
        f"🛡 *Броня:*\n{boss['recommended_armor']}\n\n"
        f"⚔ *Оружие:*\n"
        f"Воин: {boss['weapons']['warrior']}\n"
        f"Стрелок: {boss['weapons']['ranger']}\n"
        f"Маг: {boss['weapons']['mage']}\n"
        f"Призыватель: {boss['weapons']['summoner']}\n\n"
        f"🎁 *Зачем убивать:*\n{boss['progression_value']}"
    )

    await message.answer(text, reply_markup=boss_actions_kb(), parse_mode="Markdown")

# ---------- MARK AS COMPLETED ----------
@dp.message_handler(lambda m: m.text == "✅ Пройден")
async def mark_completed(message: types.Message):
    user_id = str(message.from_user.id)
    boss_key = user_current_boss.get(message.from_user.id)

    if not boss_key:
        await message.answer("❌ Сначала открой гайд на босса.")
        return

    progress = load_json(USERS_PROGRESS_PATH)
    progress.setdefault(user_id, [])

    if boss_key not in progress[user_id]:
        progress[user_id].append(boss_key)
        save_json(USERS_PROGRESS_PATH, progress)

    await message.answer("✅ Босс отмечен как пройден.")

# ---------- FAVORITES ----------
@dp.message_handler(lambda m: m.text == "⭐ В избранное")
async def add_favorite(message: types.Message):
    user_id = str(message.from_user.id)
    boss_key = user_current_boss.get(message.from_user.id)

    if not boss_key:
        await message.answer("❌ Сначала открой гайд на босса.")
        return

    favorites = load_json(FAVORITES_PATH)
    favorites.setdefault(user_id, [])

    if boss_key not in favorites[user_id]:
        favorites[user_id].append(boss_key)
        save_json(FAVORITES_PATH, favorites)

    await message.answer("⭐ Добавлено в избранное.")

# ---------- SHOW FAVORITES ----------
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    user_id = str(message.from_user.id)
    favorites = load_json(FAVORITES_PATH).get(user_id, [])

    if not favorites:
        await message.answer("⭐ Избранное пусто.")
        return

    text = "⭐ *Избранные боссы:*\n\n"
    for key in favorites:
        text += f"• {BOSSES[key]['name']}\n"

    await message.answer(text, parse_mode="Markdown")

# ---------- PROGRESS ----------
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(message: types.Message):
    user_id = str(message.from_user.id)
    progress = load_json(USERS_PROGRESS_PATH).get(user_id, [])

    total = len(BOSSES)
    done = len(progress)
    percent = int(done / total * 100) if total else 0

    text = f"📊 *Прогресс:*\n\n{done}/{total} босcов\nГотово: {percent}%"

    await message.answer(text, parse_mode="Markdown")

# ---------- BACK ----------
@dp.message_handler(lambda m: m.text == "⬅ Назад")
async def back(message: types.Message):
    await bosses_menu(message)

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)