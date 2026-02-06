import json
import os
from aiogram import Bot, Dispatcher, executor, types
from keyboards import main_menu_kb, bosses_kb, boss_actions_kb

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- ЗАГРУЗКА ДАННЫХ ----------

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

# ---------- START ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nВыбери раздел:",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ---------- ГЛАВНОЕ МЕНЮ ----------

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await message.answer("🏠 Главное меню:", reply_markup=main_menu_kb())

# ---------- БОССЫ ----------

@dp.message_handler(lambda m: m.text == "👁️ Боссы")
async def bosses_menu(message: types.Message):
    names = [boss["name"] for boss in BOSSES.values()]
    await message.answer(
        "👁️ Выбери босса:",
        reply_markup=bosses_kb(names)
    )

# ---------- ГАЙД ПО БОССУ ----------

@dp.message_handler(lambda m: any(m.text == b["name"] for b in BOSSES.values()))
async def boss_guide(message: types.Message):
    boss = next(b for b in BOSSES.values() if b["name"] == message.text)

    text = (
        f"*{boss['name']}*\n\n"
        f"⚔️ *Сложность:* {boss['difficulty']}\n"
        f"🛡 *Броня:* {boss['armor']}\n"
        f"🗡 *Оружие:* {boss['weapons']}\n"
        f"🏗 *Арена:* {boss['arena']}\n"
        f"🧠 *Тактика:* {boss['strategy']}\n"
        f"🎁 *Зачем убивать:* {boss['reason']}"
    )

    await message.answer(
        text,
        reply_markup=boss_actions_kb(),
        parse_mode="Markdown"
    )

# ---------- В ИЗБРАННОЕ ----------

@dp.message_handler(lambda m: m.text == "⭐ В избранное")
async def add_favorite(message: types.Message):
    favs = load_json("data/favorites.json")
    uid = str(message.from_user.id)
    favs.setdefault(uid, []).append(message.reply_to_message.text.split("\n")[0])
    favs[uid] = list(set(favs[uid]))
    save_json("data/favorites.json", favs)
    await message.answer("⭐ Добавлено в избранное")

@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    favs = load_json("data/favorites.json")
    uid = str(message.from_user.id)
    text = "\n".join(favs.get(uid, [])) or "Пока пусто"
    await message.answer(f"⭐ *Избранное:*\n{text}", parse_mode="Markdown")

# ---------- ПРОЙДЕН ----------

@dp.message_handler(lambda m: m.text == "✅ Пройден")
async def mark_done(message: types.Message):
    progress = load_json("data/users_progress.json")
    uid = str(message.from_user.id)
    progress.setdefault(uid, []).append(message.reply_to_message.text.split("\n")[0])
    progress[uid] = list(set(progress[uid]))
    save_json("data/users_progress.json", progress)
    await message.answer("✅ Отмечено как пройдено")

# ---------- ПРОГРЕСС ----------

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(message: types.Message):
    progress = load_json("data/users_progress.json")
    uid = str(message.from_user.id)
    done = len(progress.get(uid, []))
    total = len(BOSSES)
    percent = int((done / total) * 100) if total else 0

    await message.answer(
        f"📊 Прогресс: *{percent}%*\nПройдено: {done} из {total}",
        parse_mode="Markdown"
    )

# ---------- НАЗАД ----------

@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back(message: types.Message):
    await bosses_menu(message)

# ---------- RUN ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)