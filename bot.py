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
        with open('data/bosses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка JSON: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list:hm"))
    
    await message.answer(
        "👋 **Гайд по Terraria 1.4.5**\nВыбери этап, чтобы увидеть боссов:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("list:"))
async def show_boss_list(callback: types.CallbackQuery):
    await callback.answer()
    stage = callback.data.split(":")[1]
    data = load_data()
    
    builder = InlineKeyboardBuilder()
    for key, boss in data[stage].items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select:{stage}:{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выбери босса:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select:"))
async def boss_menu(callback: types.CallbackQuery):
    await callback.answer()
    _, stage, key = callback.data.split(":")
    
    builder = InlineKeyboardBuilder()
    # Кнопки классов
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Воин", callback_data=f"class:{stage}:{key}:warrior"),
        types.InlineKeyboardButton(text="🎯 Стрелок", callback_data=f"class:{stage}:{key}:ranger")
    )
    builder.row(
        types.InlineKeyboardButton(text="🔮 Маг", callback_data=f"class:{stage}:{key}:mage"),
        types.InlineKeyboardButton(text="🐍 Призыв", callback_data=f"class:{stage}:{key}:summoner")
    )
    # Кнопки общей инфы
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info:{stage}:{key}:tactics"),
        types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info:{stage}:{key}:drops")
    )
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list:{stage}"))
    
    data = load_data()
    boss = data[stage][key]
    await callback.message.edit_text(
        f"📖 **Гайд: {boss['name']}**\n\n{boss['general']}\n\n**Выбери категорию для подробностей:**",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("class:"))
async def show_class_info(callback: types.CallbackQuery):
    await callback.answer()
    _, stage, key, class_id = callback.data.split(":")
    data = load_data()
    boss = data[stage][key]
    
    titles = {"warrior": "Воин ⚔️", "ranger": "Стрелок 🎯", "mage": "Маг 🔮", "summoner": "Призыватель 🐍"}
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    
    await callback.message.edit_text(
        f"🛡️ **Экипировка: {titles[class_id]}**\n\n{boss['classes'][class_id]}\n\n"
        f"ℹ️ _(К) - Крафт, (Д) - Дроп, (П) - Покупка, (Н) - Найдено_",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("info:"))
async def show_general_info(callback: types.CallbackQuery):
    await callback.answer()
    _, stage, key, info_type = callback.data.split(":")
    data = load_data()
    boss = data[stage][key]
    
    titles = {"tactics": "⚔️ Тактика и Арена", "drops": "🎁 Дроп и Шансы"}
    content = boss['tactics'] + "\n\n**Арена:** " + boss['arena'] if info_type == "tactics" else boss['drops']
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    
    await callback.message.edit_text(
        f"**{titles[info_type]}**\n\n{content}",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

