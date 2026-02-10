import os
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Загрузка данных
def load_bosses():
    with open('data/bosses.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- КОМАНДА ЗАПУСКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list_hm"))
    
    # ReplyKeyboardRemove() удалит те самые старые кнопки с Гидом и Торговцем
    await message.answer(
        "👋 **Привет! Я твой гид по Terraria 1.4.5.**\n\n"
        "Выбери этап игры для просмотра боссов:",
        reply_markup=types.ReplyKeyboardRemove() # Удаляем старые кнопки
    )
    # Отправляем новое меню
    await message.answer("Меню навигации:", reply_markup=builder.as_markup())

# --- СПИСОК БОССОВ ---
@dp.callback_query(F.data.startswith("list_"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split("_")[1] # pre_hm или hm
    data = load_bosses().get(stage, {})
    
    builder = InlineKeyboardBuilder()
    for key, boss in data.items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select_{stage}_{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "👹 **Выберите босса:**", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )

# --- ИНФОРМАЦИЯ О БОССЕ (ПОД КНОПКИ) ---
@dp.callback_query(F.data.startswith("select_"))
async def boss_menu(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    # Исправленная логика извлечения ключей
    stage = f"{parts[1]}_{parts[2]}" 
    key = "_".join(parts[3:])
    
    boss_data = load_bosses()[stage][key]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🛡️ Экип", callback_data=f"info_{stage}_{key}_gear"),
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info_{stage}_{key}_tactics")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info_{stage}_{key}_drops"),
        types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"info_{stage}_{key}_arena")
    )
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list_{stage}"))
    
    await callback.message.edit_text(
        f"📖 **Гайд: {boss_data['name']}**\n\n{boss_data['general']}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- ВЫВОД КОНКРЕТНОГО РАЗДЕЛА ---
@dp.callback_query(F.data.startswith("info_"))
async def display_info(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    section = parts[-1]
    stage = f"{parts[1]}_{parts[2]}"
    key = "_".join(parts[3:-1])
    
    boss = load_bosses()[stage][key]
    titles = {"gear": "🛡️ Экипировка", "tactics": "⚔️ Тактика", "drops": "🎁 Дроп", "arena": "🏟️ Арена"}
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_{stage}_{key}"))
    
    await callback.message.edit_text(
        f"**{boss['name']} — {titles[section]}**\n\n{boss[section]}", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
