import os
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Загрузка JSON данных
def load_bosses():
    path = 'data/bosses.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list_hm"))
    
    await message.answer(
        "🌳 **Добро пожаловать в гайд по Terraria 1.4.5!**\n\n"
        "Выберите этап игры, чтобы увидеть список боссов:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("list_"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split("_")[1] # pre_hm или hm
    data = load_bosses().get(stage, {})
    
    builder = InlineKeyboardBuilder()
    for key, boss in data.items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select_{stage}_{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    
    title = "🟢 Боссы До-Хардмода" if stage == "pre_hm" else "🔴 Боссы Хардмода"
    await callback.message.edit_text(f"**{title}:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("select_"))
async def boss_menu(callback: types.CallbackQuery):
    # data format: select_pre_hm_eye_of_cthulhu
    parts = callback.data.split("_")
    stage = f"{parts[1]}_{parts[2]}"
    key = "_".join(parts[3:])
    
    boss_name = load_bosses()[stage][key]['name']
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"info_{stage}_{key}_gear"),
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info_{stage}_{key}_tactics")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info_{stage}_{key}_drops"),
        types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"info_{stage}_{key}_arena")
    )
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку боссов", callback_data=f"list_{stage}"))
    
    await callback.message.edit_text(
        f"📖 **Гайд: {boss_name}**\n\n{load_bosses()[stage][key]['general']}\n\nЧто именно тебя интересует?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("info_"))
async def display_info(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    # info_pre_hm_eye_of_cthulhu_gear
    stage = f"{parts[1]}_{parts[2]}"
    section = parts[-1]
    key = "_".join(parts[3:-1])
    
    boss = load_bosses()[stage][key]
    
    titles = {"gear": "🛡️ Экипировка", "tactics": "⚔️ Тактика", "drops": "🎁 Дроп", "arena": "🏟️ Арена"}
    
    response_text = f"**{boss['name']} — {titles[section]}**\n\n{boss[section]}"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_{stage}_{key}"))
    
    await callback.message.edit_text(response_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list_hm"))
    await callback.message.edit_text("🌳 **Выберите этап игры:**", reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
