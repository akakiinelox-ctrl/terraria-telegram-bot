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

# Безопасная загрузка данных
def load_data(category):
    try:
        # Пытаемся открыть файл. Проверь, что путь на GitHub именно такой!
        path = f"data/{category}.json"
        if not os.path.exists(path):
            logging.error(f"Файл не найден: {path}")
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки JSON: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list_hm"))
    
    # Сначала удаляем старые Reply-кнопки (Гид, Торговец), если они есть
    await message.answer("🛠 Подготовка меню...", reply_markup=types.ReplyKeyboardRemove())
    # Затем отправляем основное меню
    await message.answer("🌳 **Выбери этап игры для изучения боссов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("list_"))
async def show_boss_list(callback: types.CallbackQuery):
    # Убираем "Загрузку" сразу, чтобы кнопка не висела
    await callback.answer()
    
    stage = callback.data.replace("list_", "") # "pre_hm" или "hm"
    all_data = load_data("bosses")
    
    if not all_data or stage not in all_data:
        await callback.message.answer("❌ Ошибка: Не удалось загрузить список боссов. Проверь файл data/bosses.json")
        return

    data = all_data[stage]
    builder = InlineKeyboardBuilder()
    for key, boss in data.items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select_{stage}_{key}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    
    await callback.message.edit_text("👹 **Выбери босса:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select_"))
async def boss_options(callback: types.CallbackQuery):
    await callback.answer()
    
    try:
        # Разбиваем select_pre_hm_king_slime
        parts = callback.data.split("_")
        stage = f"{parts[1]}_{parts[2]}" # pre_hm
        key = "_".join(parts[3:])        # king_slime
        
        all_data = load_data("bosses")
        boss = all_data[stage][key]
        
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
            f"📖 **Гайд: {boss['name']}**\n\n{boss.get('general', 'Информация скоро будет добавлена.')}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка в select_: {e}")
        await callback.message.answer("⚠️ Произошла ошибка при открытии меню босса.")

@dp.callback_query(F.data.startswith("info_"))
async def display_info(callback: types.CallbackQuery):
    await callback.answer()
    
    try:
        parts = callback.data.split("_")
        section = parts[-1]              # gear, tactics и т.д.
        stage = f"{parts[1]}_{parts[2]}" # pre_hm
        key = "_".join(parts[3:-1])      # boss_key
        
        all_data = load_data("bosses")
        boss = all_data[stage][key]
        
        titles = {"gear": "🛡️ Экипировка", "tactics": "⚔️ Тактика", "drops": "🎁 Дроп", "arena": "🏟️ Арена"}
        
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_{stage}_{key}"))
        
        await callback.message.edit_text(
            f"**{boss['name']} — {titles[section]}**\n\n{boss[section]}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.answer("⚠️ Ошибка при отображении информации.")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
