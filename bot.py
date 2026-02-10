import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логов для отслеживания ошибок в консоли Railway
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

def load_bosses():
    # [span_6](start_span)[span_7](start_span)Путь к файлу согласно твоей структуре[span_6](end_span)[span_7](end_span)
    with open('data/bosses.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list_hm"))
    
    # ReplyKeyboardRemove() убирает старые кнопки (Гид, Торговец), которые видны на скриншоте
    await message.answer(
        "👋 **Привет! Я твой гайд по Terraria 1.4.5.**",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer("Выбери этап игры:", reply_markup=builder.as_markup())

# Показ списка боссов
@dp.callback_query(F.data.startswith("list_"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split("_")[1] + "_" + callback.data.split("_")[2] # "pre_hm" или "hm"
    data = load_bosses().get(stage, {})
    
    builder = InlineKeyboardBuilder()
    for key, boss in data.items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select_{stage}_{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    
    await callback.answer() # Убирает "Загрузку..."
    await callback.message.edit_text("👹 **Выбери босса:**", reply_markup=builder.as_markup())

# Меню выбора разделов босса
@dp.callback_query(F.data.startswith("select_"))
async def boss_options(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    # select_pre_hm_king_slime -> stage="pre_hm", key="king_slime"
    stage = f"{parts[1]}_{parts[2]}"
    key = "_".join(parts[3:])
    
    boss = load_bosses()[stage][key]
    
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
    
    await callback.answer()
    await callback.message.edit_text(
        f"📖 **Гайд: {boss['name']}**\n\n{boss.get('general', '')}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Вывод детальной инфы
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
    
    await callback.answer()
    await callback.message.edit_text(
        f"**{boss['name']} — {titles[section]}**\n\n{boss[section]}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
