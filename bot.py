import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

def load_data():
    try:
        # Убедись, что файл на GitHub именно по этому пути
        with open('data/bosses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки JSON: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list:hm"))
    
    # ReplyKeyboardRemove уберет кнопки "Гид", "Торговец" и т.д.
    await message.answer(
        "👋 **Привет! Я твой гид по Terraria 1.4.5.**\nВыбери этап игры:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("list:"))
async def show_boss_list(callback: types.CallbackQuery):
    await callback.answer()
    stage = callback.data.split(":")[1]
    data = load_data()
    
    if not data or stage not in data:
        await callback.message.answer("❌ Ошибка данных.")
        return

    builder = InlineKeyboardBuilder()
    for key, boss in data[stage].items():
        # Используем двоеточие как разделитель, чтобы не путать с нижним подчеркиванием
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select:{stage}:{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text(f"👹 **Список боссов ({stage}):**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select:"))
async def boss_options(callback: types.CallbackQuery):
    await callback.answer()
    _, stage, key = callback.data.split(":")
    
    data = load_data()
    boss = data[stage][key]
    
    builder = InlineKeyboardBuilder()
    # Формируем кнопки инфо
    for info_key, label in [("gear", "🛡️ Экип"), ("tactics", "⚔️ Тактика"), ("drops", "🎁 Дроп"), ("arena", "🏟️ Арена")]:
        builder.add(types.InlineKeyboardButton(text=label, callback_data=f"info:{stage}:{key}:{info_key}"))
    
    builder.adjust(2) # Кнопки в 2 ряда
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list:{stage}"))
    
    await callback.message.edit_text(
        f"📖 **Гайд: {boss['name']}**\n\n{boss.get('general', '')}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("info:"))
async def display_info(callback: types.CallbackQuery):
    await callback.answer()
    _, stage, key, section = callback.data.split(":")
    
    data = load_data()
    boss = data[stage][key]
    
    titles = {"gear": "🛡️ Экипировка", "tactics": "⚔️ Тактика", "drops": "🎁 Дроп", "arena": "🏟️ Арена"}
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    
    await callback.message.edit_text(
        f"**{boss['name']} — {titles[section]}**\n\n{boss[section]}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    # Сбрасываем в начало
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list:hm"))
    await callback.message.edit_text("Выбери этап игры:", reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
