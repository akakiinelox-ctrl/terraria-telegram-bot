import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ================== TOKEN ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================== PATHS ==================
BOSSES_PATH = "data/bosses.json"
PROGRESS_PATH = "data/users_progress.json"
FAVORITES_PATH = "data/favorites.json"

# ================== HELPERS ==================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== LOAD DATA ==================
with open(BOSSES_PATH, encoding="utf-8") as f:
    BOSSES = json.load(f)

# ================== MAP NAME -> KEY ==================
BOSS_NAME_MAP = {
    "Король слизней": "king_slime",
    "Глаз Ктулху": "eye_of_cthulhu",
    "Пожиратель миров": "eater_of_worlds",
    "Мозг Ктулху": "brain_of_cthulhu",
    "Королева пчёл": "queen_bee",
    "Скелетрон": "skeletron",
    "Стена плоти": "wall_of_flesh"
}

# ================== KEYBOARDS ==================
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("⭐ Избранное", "📊 Прогресс")
    return kb

def bosses_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        kb.add(boss["name"])
    kb.add("🏠 Главное меню")
    return kb

def boss_actions_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Пройден", "⭐ В избранное")
    kb.add("⬅️ Назад")
    return kb

# ================== START / MAIN ==================
@dp.message_handler(commands=["start"])
@dp.message_handler(lambda m: m.text in ("🏠 Главное меню",))
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Полные гайды по боссам Terraria.\n"
        "Используй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ================== BOSSES MENU ==================
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 Выбери босса:",
        reply_markup=bosses_kb()
    )

# ================== BOSS GUIDE ==================
@dp.message_handler(lambda m: any(name in m.text for name in BOSS_NAME_MAP))
async def boss_guide(message: types.Message):
    boss_key = None
    for name, key in BOSS_NAME_MAP.items():
        if name in message.text:
            boss_key = key
            break

    if not boss_key:
        return

    boss = BOSSES[boss_key]

    text = (
        f"🔥 *{boss['name']}*\n"
        f"⚙ Стадия: {boss['stage']}\n"
        f"⚔ Сложность: {boss['difficulty']}\n\n"
        f"🚨 *Угрозы:*\n{boss['threat_profile']}\n\n"
        f"❤️ *Минимум:* {boss['minimum_requirements']}\n"
        f"🛡 *Броня:* {boss['recommended_armor']}\n"
        f"📦 *Ресурсы:* {boss['required_resources']}\n\n"
        f"⚔ *Оружие по классам:*\n"
        f"• Воин: {boss['weapons']['warrior']}\n"
        f"• Стрелок: {boss['weapons']['ranger']}\n"
        f"• Маг: {boss['weapons']['mage']}\n"
        f"• Призыватель: {boss['weapons']['summoner']}\n\n"
        f"🏗 *Арена:* {boss['arena_blueprint']}\n"
        f"🧠 *Поведение:* {boss['boss_behavior']}\n"
        f"💥 *Окна урона:* {boss['damage_windows']}\n"
        f"❌ *Частые ошибки:* {boss['common_failures']}\n"
        f"🛠 *Как исправить:* {boss['recovery_plan']}\n\n"
        f"📈 *Значение:* {boss['progression_value']}"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=boss_actions_kb()
    )

# ================== MARK COMPLETED ==================
@dp.message_handler(lambda m: m.text == "✅ Пройден")
async def mark_completed(message: types.Message):
    if not message.reply_to_message:
        return

    user_id = str(message.from_user.id)
    progress = load_json(PROGRESS_PATH)
    progress.setdefault(user_id, [])

    boss_line = message.reply_to_message.text.split("\n")[0]
    boss_name = boss_line.replace("*", "").strip()

    if boss_name not in progress[user_id]:
        progress[user_id].append(boss_name)
        save_json(PROGRESS_PATH, progress)
        await message.answer("✅ Босс отмечен как пройден")
    else:
        await message.answer("ℹ️ Этот босс уже отмечен")

# ================== FAVORITES ==================
@dp.message_handler(lambda m: m.text == "⭐ В избранное")
async def toggle_favorite(message: types.Message):
    if not message.reply_to_message:
        return

    user_id = str(message.from_user.id)
    favorites = load_json(FAVORITES_PATH)
    favorites.setdefault(user_id, [])

    boss_line = message.reply_to_message.text.split("\n")[0]
    boss_name = boss_line.replace("*", "").strip()

    if boss_name in favorites[user_id]:
        favorites[user_id].remove(boss_name)
        await message.answer("❌ Убрано из избранного")
    else:
        favorites[user_id].append(boss_name)
        await message.answer("⭐ Добавлено в избранное")

    save_json(FAVORITES_PATH, favorites)

# ================== SHOW FAVORITES ==================
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    user_id = str(message.from_user.id)
    favorites = load_json(FAVORITES_PATH).get(user_id, [])

    if not favorites:
        await message.answer("⭐ Избранное пусто", reply_markup=main_menu_kb())
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for name in favorites:
        kb.add(name)
    kb.add("🏠 Главное меню")

    await message.answer("⭐ Твои избранные боссы:", reply_markup=kb)

# ================== PROGRESS ==================
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def show_progress(message: types.Message):
    user_id = str(message.from_user.id)
    progress = load_json(PROGRESS_PATH).get(user_id, [])

    total = len(BOSSES)
    done = len(progress)
    percent = int(done / total * 100) if total else 0

    bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)

    text = (
        f"📊 *Прогресс*\n\n"
        f"{bar} {percent}%\n"
        f"Пройдено: {done}/{total}"
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_kb())

# ================== BACK ==================
@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back_to_bosses(message: types.Message):
    await bosses_menu(message)

# ================== FALLBACK ==================
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer(
        "Используй кнопки 👇",
        reply_markup=main_menu_kb()
    )

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)