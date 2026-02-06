import json
from aiogram import Bot, Dispatcher, executor, types
from keyboards import main_menu_kb, bosses_kb

BOT_TOKEN = "8513031435:AAHfTK010ez5t5rYBXx5FxO5l-xRHZ8wZew"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------- ЗАГРУЗКА ДАННЫХ ----------
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

# ---------- СООТВЕТСТВИЕ КНОПОК → КЛЮЧИ JSON ----------
BOSS_BUTTON_MAP = {
    "🟢👑 Король слизней": "king_slime",
    "🔴👁 Глаз Ктулху": "eye_of_cthulhu",
    "🟡🐛 Пожиратель миров": "eater_of_worlds",
    "🟣🧠 Мозг Ктулху": "brain_of_cthulhu",
    "🟠🐝 Королева пчёл": "queen_bee",
    "⚪💀 Скелетрон": "skeletron",
    "🔴🔥 Стена плоти": "wall_of_flesh",
}

# ---------- START ----------
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nИспользуй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ---------- ГЛАВНОЕ МЕНЮ ----------
@dp.message_handler(lambda m: m.text == "⬅ Назад")
@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_kb()
    )

# ---------- БОССЫ ----------
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 Выбери босса:",
        reply_markup=bosses_kb()
    )

# ---------- ГАЙД ПО БОССУ ----------
@dp.message_handler(lambda m: m.text in BOSS_BUTTON_MAP)
async def boss_guide(message: types.Message):
    boss_key = BOSS_BUTTON_MAP[message.text]
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
        f"📈 *Прогресс:* {boss['progression_value']}"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=bosses_kb()
    )

# ---------- ЗАГЛУШКИ ----------
@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def fav(message: types.Message):
    await message.answer("⭐ Избранное\n\nВ разработке 👷", reply_markup=main_menu_kb())

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(message: types.Message):
    await message.answer("📊 Прогресс\n\nСкоро будет 👀", reply_markup=main_menu_kb())

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)