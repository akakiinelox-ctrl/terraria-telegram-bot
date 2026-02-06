import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================== DATA ==================
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

FAVORITES_PATH = "data/favorites.json"
PROGRESS_PATH = "data/users_progress.json"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== KEYBOARDS ==================
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👁 Боссы")
    kb.add("⭐ Избранное", "📊 Прогресс")
    return kb

def bosses_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, boss in BOSSES.items():
        kb.add(
            types.InlineKeyboardButton(
                text=boss["name"],
                callback_data=f"boss:{key}"
            )
        )
    return kb

def boss_actions_kb(boss_key, is_fav, is_done):
    kb = types.InlineKeyboardMarkup(row_width=2)

    if is_fav:
        kb.add(types.InlineKeyboardButton("❌ Убрать из избранного", callback_data=f"unfav:{boss_key}"))
    else:
        kb.add(types.InlineKeyboardButton("⭐ В избранное", callback_data=f"fav:{boss_key}"))

    if is_done:
        kb.add(types.InlineKeyboardButton("☑️ Пройдено", callback_data="noop"))
    else:
        kb.add(types.InlineKeyboardButton("✅ Отметить пройденным", callback_data=f"done:{boss_key}"))

    kb.add(
        types.InlineKeyboardButton("↩ Назад", callback_data="back:bosses"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back:menu")
    )
    return kb

# ================== TEXT ==================
def render_boss(boss):
    return (
        f"*{boss['name']}*\n\n"
        f"⚔ *Сложность:* {boss['difficulty']}\n"
        f"🧱 *Этап:* {boss['stage']}\n\n"
        f"🛡 *Броня:*\n{boss['armor']}\n\n"
        f"⚔ *Оружие:*\n{boss['weapons']}\n\n"
        f"🏗 *Арена:*\n{boss['arena']}\n\n"
        f"🧠 *Тактика:*\n{boss['strategy']}\n\n"
        f"🎁 *Зачем убивать:*\n{boss['reason']}"
    )

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nПолностью кнопочный гайд по игре.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ================== BOSSES ==================
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 *Боссы Terraria:*",
        reply_markup=bosses_inline_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("boss:"))
async def show_boss(call: types.CallbackQuery):
    boss_key = call.data.split(":")[1]
    boss = BOSSES[boss_key]

    uid = str(call.from_user.id)
    favs = load_json(FAVORITES_PATH).get(uid, [])
    done = load_json(PROGRESS_PATH).get(uid, [])

    await call.message.edit_text(
        render_boss(boss),
        reply_markup=boss_actions_kb(
            boss_key,
            boss_key in favs,
            boss_key in done
        ),
        parse_mode="Markdown"
    )
    await call.answer()

# ================== FAVORITES ==================
@dp.callback_query_handler(lambda c: c.data.startswith("fav:"))
async def add_fav(call: types.CallbackQuery):
    boss_key = call.data.split(":")[1]
    uid = str(call.from_user.id)

    favs = load_json(FAVORITES_PATH)
    favs.setdefault(uid, [])
    if boss_key not in favs[uid]:
        favs[uid].append(boss_key)
        save_json(FAVORITES_PATH, favs)

    await call.answer("⭐ Добавлено")
    await show_boss(call)

@dp.callback_query_handler(lambda c: c.data.startswith("unfav:"))
async def remove_fav(call: types.CallbackQuery):
    boss_key = call.data.split(":")[1]
    uid = str(call.from_user.id)

    favs = load_json(FAVORITES_PATH)
    if boss_key in favs.get(uid, []):
        favs[uid].remove(boss_key)
        save_json(FAVORITES_PATH, favs)

    await call.answer("❌ Убрано")
    await show_boss(call)

# ================== DONE ==================
@dp.callback_query_handler(lambda c: c.data.startswith("done:"))
async def mark_done(call: types.CallbackQuery):
    boss_key = call.data.split(":")[1]
    uid = str(call.from_user.id)

    prog = load_json(PROGRESS_PATH)
    prog.setdefault(uid, [])
    if boss_key not in prog[uid]:
        prog[uid].append(boss_key)
        save_json(PROGRESS_PATH, prog)

    await call.answer("✅ Отмечено")
    await show_boss(call)

@dp.callback_query_handler(lambda c: c.data == "noop")
async def noop(call: types.CallbackQuery):
    await call.answer()

# ================== NAV ==================
@dp.callback_query_handler(lambda c: c.data == "back:bosses")
async def back_bosses(call: types.CallbackQuery):
    await call.message.edit_text(
        "👁 *Боссы Terraria:*",
        reply_markup=bosses_inline_kb(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "back:menu")
async def back_menu(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer("Главное меню:", reply_markup=main_menu_kb())
    await call.answer()

# ================== PROGRESS ==================
@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(message: types.Message):
    uid = str(message.from_user.id)
    done = load_json(PROGRESS_PATH).get(uid, [])

    total = len(BOSSES)
    percent = int(len(done) / total * 100) if total else 0
    bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)

    await message.answer(
        f"📊 *Прогресс*\n\n{bar} {percent}%\nПройдено: {len(done)}/{total}",
        parse_mode="Markdown"
    )

# ================== FAVORITES MENU ==================
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def favorites_menu(message: types.Message):
    uid = str(message.from_user.id)
    favs = load_json(FAVORITES_PATH).get(uid, [])

    if not favs:
        await message.answer("⭐ Избранное пусто")
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for key in favs:
        kb.add(types.InlineKeyboardButton(BOSSES[key]["name"], callback_data=f"boss:{key}"))

    await message.answer("⭐ *Избранное:*", reply_markup=kb, parse_mode="Markdown")

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)