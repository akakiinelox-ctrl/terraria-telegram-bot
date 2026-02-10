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
    await message.answer("Выбери этап игры:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("list:"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = load_data()
    builder = InlineKeyboardBuilder()
    for key, boss in data[stage].items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("👹 Выбери босса:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select:"))
async def boss_main_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    data = load_data()
    boss = data[stage][key]
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экип", callback_data=f"gear_menu:{stage}:{key}"))
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info:{stage}:{key}:tactics"),
        types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"info:{stage}:{key}:arena")
    )
    builder.row(types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info:{stage}:{key}:drops"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list:{stage}"))
    
    await callback.message.edit_text(f"📖 **Гайд: {boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("gear_menu:"))
async def gear_classes_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Воин", callback_data=f"class_gear:{stage}:{key}:warrior"),
        types.InlineKeyboardButton(text="🎯 Стрелок", callback_data=f"class_gear:{stage}:{key}:ranger")
    )
    builder.row(
        types.InlineKeyboardButton(text="🔮 Маг", callback_data=f"class_gear:{stage}:{key}:mage"),
        types.InlineKeyboardButton(text="🐍 Призыв", callback_data=f"class_gear:{stage}:{key}:summoner")
    )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text("🛡️ **Выбери свой класс:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("class_gear:"))
async def show_items_as_buttons(callback: types.CallbackQuery):
    _, stage, key, class_id = callback.data.split(":")
    data = load_data()
    items = data[stage][key]['classes'][class_id] # Теперь это список словарей
    
    builder = InlineKeyboardBuilder()
    for item in items:
        # При нажатии покажет всплывающее окно
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"item_craft:{stage}:{key}:{class_id}:{items.index(item)}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"gear_menu:{stage}:{key}"))
    await callback.message.edit_text(f"🎒 **Снаряжение ({class_id}):**\nНажми на предмет, чтобы узнать крафт.", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("item_craft:"))
async def show_craft_alert(callback: types.CallbackQuery):
    _, stage, key, class_id, item_index = callback.data.split(":")
    data = load_data()
    item = data[stage][key]['classes'][class_id][int(item_index)]
    
    # Показываем уведомление прямо в Telegram (show_alert=True делает окно с кнопкой OK)
    await callback.answer(f"🛠 {item['name']}:\n{item['craft']}", show_alert=True)

@dp.callback_query(F.data.startswith("info:"))
async def show_other_info(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    data = load_data()
    boss = data[stage][key]
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text(f"📝 **{field.capitalize()}:**\n\n{boss[field]}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
