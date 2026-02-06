import json
from aiogram import Bot, Dispatcher, executor, types

from keyboards import main_menu_kb, bosses_kb, back_menu_kb


BOT_TOKEN = "ТОКЕН_ТУТ"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# ---------- ЗАГРУЗКА ДАННЫХ ----------

with open("data/bosses.json", encoding="utf-8") as f:
    BOSSES = json.load(f)


# ---------- START ----------

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\nПолные гайды по Terraria.\nИспользуй кнопки 👇",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


# ---------- ГЛАВНОЕ МЕНЮ ----------

@dp.message_handler(lambda m: m.text == "🏠 Главное меню")
async def main_menu(message: types.Message):
    await message.answer(
        "Главное меню:",
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

@dp.message_handler(lambda m: m.text in BOSSES)
async def boss_guide(message: types.Message):
    boss = BOSSES[message.text]

    text = (
        f"{boss['icon']} *{message.text}*\n"
        f"{boss['difficulty']}\n\n"
        f"🎯 *Зачем убивать:*\n{boss['reason']}\n\n"
        f"🛡 *Броня:*\n{boss['armor']}\n\n"
        f"⚔️ *Оружие:*\n{boss['weapons']}\n\n"
        f"🏗 *Арена:*\n{boss['arena']}\n\n"
        f"🧠 *Тактика:*\n{boss['strategy']}"
    )

    await message.answer(
        text,
        reply_markup=back_menu_kb(),
        parse_mode="Markdown"
    )

    return  # 🔥 КЛЮЧЕВО: НЕ ОТКАТЫВАЕТСЯ НАЗАД


# ---------- ИЗБРАННОЕ ----------

@dp.message_handler(lambda m: m.text == "⭐ Избранное")
async def favorites(message: types.Message):
    await message.answer(
        "⭐ Избранное\n\nПока в разработке 👷‍♂️",
        reply_markup=main_menu_kb()
    )


# ---------- ПРОГРЕСС ----------

@dp.message_handler(lambda m: m.text == "📊 Прогресс")
async def progress(message: types.Message):
    await message.answer(
        "📊 Прогресс\n\nФункция в разработке 🚧",
        reply_markup=main_menu_kb()
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)