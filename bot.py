import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ===== DATA =====
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

FAV_PATH = "data/favorites.json"
PROG_PATH = "data/users_progress.json"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== KEYBOARDS =====
def main_menu_kb():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "👁 Боссы", "⭐ Избранное", "📊 Прогресс"
    )

def bosses_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, boss in BOSSES.items():
        kb.add(types.InlineKeyboardButton(
            text=boss["name"],
            callback_data=f"boss:{key}"
        ))
    return kb

def boss_actions_kb(boss_key, is_fav, is_done):
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(types.InlineKeyboardButton(
        "❌ Убрать из избранного" if is_fav else "⭐ В избранное",
        callback_data=f"{'unfav' if is_fav else 'fav'}:{boss_key}"
    ))

    kb.add(types.InlineKeyboardButton(
        "☑️ Пройдено" if is_done else "✅ Отметить пройденным",
        callback_data="noop" if is_done else f"done:{boss_key}"
    ))

    kb.add(
        types.InlineKeyboardButton("↩ Назад", callback_data="back:bosses"),
        types.InlineKeyboardButton("🏠 Меню", callback_data="back:menu")
    )
    return kb

# ===== TEXT =====
def render_boss(b):
    return (
        f"*{b['name']}*\n\n"
        f"⚔ *Сложность:* {b['difficulty']}\n"
        f"🧱 *Этап:* {b['stage']}\n\n"
        f"⚠️ *Опасности:*\n{b['threat_profile']}\n\n"
        f"🛡 *Минимум:* {b['minimum_requirements']}\n"
        f"🛡 *Броня:* {b['recommended_armor']}\n"
        f"📦 *Ресурсы:* {b['required_resources']}\n\n"
        f"⚔ *Оружие:*\n"
        f"• Воин: {b['weapons']['warrior']}\n"
        f"• Стрелок: {b['weapons']['ranger']}\n"
        f"• Маг: {b['weapons']['mage']}\n"
        f"• Призыватель: {b['weapons']['summoner']}\n\n"
        f"🏗 *Арена:* {b['arena_blueprint']}\n\n"
        f"🧠 *Тактика:* {b['boss_behavior']}\n"
        f"🎯 *Окна урона:* {b['damage_windows']}\n"
        f"❌ *Ошибки:* {b['common_failures']}\n"
        f"🔁 *Если не вышло:* {b['recovery_plan']}\n\n"
        f"🎁 *Зачем убивать:* {b['progression_value']}"
    )

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    await m.answer(
        "🎮 *Terraria Guide Bot*\n\nПолный кнопочный гайд.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ===== BOSSES =====
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(m: types.Message):
    await m.answer(
        "👁 *Боссы:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("boss:"))
async def show_boss(c: types.CallbackQuery):
    key = c.data.split(":")[1]
    boss = BOSSES[key]

    uid = str(c.from_user.id)
    favs = load_json(FAV_PATH).get(uid, [])
    done = load_json(PROG_PATH).get(uid, [])

    await c.message.edit_text(
        render_boss(boss),
        parse_mode="Markdown",
        reply_markup=boss_actions_kb(
            key,
            key in favs,
            key in done
        )
    )
    await c.answer()

# ===== FAVORITES =====
@dp.callback_query_handler(lambda c: c.data.startswith("fav:"))
async def fav_add(c):
    key = c.data.split(":")[1]
    uid = str(c.from_user.id)
    data = load_json(FAV_PATH)
    data.setdefault(uid, [])
    if key not in data[uid]:
        data[uid].append(key)
        save_json(FAV_PATH, data)
    await c.answer("⭐ Добавлено")
    await show_boss(c)

@dp.callback_query_handler(lambda c: c.data.startswith("unfav:"))
async def fav_del(c):
    key = c.data.split(":")[1]
    uid = str(c.from_user.id)
    data = load_json(FAV_PATH)
    if key in data.get(uid, []):
        data[uid].remove(key)
        save_json(FAV_PATH, data)
    await c.answer("❌ Убрано")
    await show_boss(c)

# ===== DONE =====
@dp.callback_query_handler(lambda c: c.data.startswith("done:"))
async def mark_done(c):
    key = c.data.split(":")[1]
    uid = str(c.from_user.id)
    data = load_json(PROG_PATH)
    data.setdefault(uid, [])
    if key not in data[uid]:
        data[uid].append(key)
        save_json(PROG_PATH, data)
    await c.answer("✅ Отмечено")
    await show_boss(c)

@dp.callback_query_handler(lambda c: c.data == "noop")
async def noop(c):
    await c.answer()

# ===== NAV =====
@dp.callback_query_handler(lambda c: c.data == "back:bosses")
async def back_bosses(c):
    await c.message.edit_text(
        "👁 *Боссы:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )
    await c.answer()

@dp.callback_query_handler(lambda c: c.data == "back:menu")
async def back_menu(c):
    await c.message.delete()
    await c.message.answer("Главное меню:", reply_markup=main_menu_kb())
    await c.answer()

# ===== PROGRESS =====
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(m):
    uid = str(m.from_user.id)
    done = load_json(PROG_PATH).get(uid, [])
    total = len(BOSSES)
    pct = int(len(done) / total * 100) if total else 0
    bar = "🟩" * (pct // 10) + "⬜" * (10 - pct // 10)
    await m.answer(
        f"📊 *Прогресс*\n\n{bar} {pct}%\nПройдено: {len(done)}/{total}",
        parse_mode="Markdown"
    )

# ===== FAVORITES MENU =====
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def fav_menu(m):
    uid = str(m.from_user.id)
    favs = load_json(FAV_PATH).get(uid, [])
    if not favs:
        await m.answer("⭐ Избранное пусто")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k in favs:
        kb.add(types.InlineKeyboardButton(BOSSES[k]["name"], callback_data=f"boss:{k}"))
    await m.answer("⭐ *Избранное:*", reply_markup=kb, parse_mode="Markdown")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)