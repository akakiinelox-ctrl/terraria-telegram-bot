import json
import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ===== LOAD DATA =====
with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)

BOSS_NAMES = {boss["name"]: key for key, boss in BOSSES.items()}

# ===== STATE (простой, без FSM) =====
user_state = {}  # user_id -> boss_key

# ===== KEYBOARDS =====
def main_menu_kb():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "👁 Боссы", "ℹ️ О боте"
    )

def bosses_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for boss in BOSSES.values():
        kb.add(boss["name"])
    kb.add("⬅ Назад")
    return kb

def boss_sections_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⚔ Сложность и этап", "⚠ Опасности")
    kb.add("🛡 Подготовка", "⚔ Оружие")
    kb.add("🏗 Арена", "🧠 Тактика")
    kb.add("🎁 Зачем убивать")
    kb.add("⬅ Назад к боссам")
    return kb

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Выбирай, что хочешь узнать 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

# ===== ABOUT =====
@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about(message: types.Message):
    await message.answer(
        "📘 *Terraria Guide Bot*\n\n"
        "Интерактивные гайды по боссам Terraria.\n"
        "Без полотен текста — всё по разделам.",
        parse_mode="Markdown"
    )

# ===== BOSSES LIST =====
@dp.message_handler(lambda m: m.text == "👁 Боссы")
async def bosses_menu(message: types.Message):
    await message.answer(
        "👁 *Выбери босса:*",
        reply_markup=bosses_kb(),
        parse_mode="Markdown"
    )

# ===== BOSS SELECT =====
@dp.message_handler(lambda m: m.text in BOSS_NAMES)
async def select_boss(message: types.Message):
    boss_key = BOSS_NAMES[message.text]
    user_state[message.from_user.id] = boss_key

    boss = BOSSES[boss_key]

    await message.answer(
        f"*{boss['name']}*\n\n"
        "Выбери раздел гайда 👇",
        reply_markup=boss_sections_kb(),
        parse_mode="Markdown"
    )

# ===== SECTIONS =====
@dp.message_handler(lambda m: m.text.startswith(("⚔", "⚠", "🛡", "🏗", "🧠", "🎁")))
async def boss_section(message: types.Message):
    uid = message.from_user.id
    if uid not in user_state:
        return

    boss = BOSSES[user_state[uid]]

    sections = {
        "⚔ Сложность и этап":
            f"⚔ *Сложность:* {boss['difficulty']}\n"
            f"🧱 *Этап:* {boss['stage']}",

        "⚠ Опасности":
            boss["threat_profile"],

        "🛡 Подготовка":
            f"*Минимум:*\n{boss['minimum_requirements']}\n\n"
            f"*Рекомендуемая броня:*\n{boss['recommended_armor']}",

        "⚔ Оружие":
            f"• Воин: {boss['weapons']['warrior']}\n"
            f"• Стрелок: {boss['weapons']['ranger']}\n"
            f"• Маг: {boss['weapons']['mage']}\n"
            f"• Призыватель: {boss['weapons']['summoner']}",

        "🏗 Арена":
            boss["arena_blueprint"],

        "🧠 Тактика":
            f"{boss['boss_behavior']}\n\n"
            f"*Окна урона:* {boss['damage_windows']}\n"
            f"*Частые ошибки:* {boss['common_failures']}\n"
            f"*Если не вышло:* {boss['recovery_plan']}",

        "🎁 Зачем убивать":
            boss["progression_value"]
    }

    text = sections.get(message.text)
    if text:
        await message.answer(
            f"*{message.text}*\n\n{text}",
            parse_mode="Markdown"
        )

# ===== NAVIGATION =====
@dp.message_handler(lambda m: m.text == "⬅ Назад к боссам")
async def back_to_bosses(message: types.Message):
    user_state.pop(message.from_user.id, None)
    await bosses_menu(message)

@dp.message_handler(lambda m: m.text == "⬅ Назад")
async def back_to_menu(message: types.Message):
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_kb()
    )

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)