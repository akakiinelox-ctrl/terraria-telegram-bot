import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_boss_data():
    with open('data/bosses.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🗡️ Гайды по Классам", callback_data="menu_classes"))
    builder.row(types.InlineKeyboardButton(text="👹 Боссы (Порядок)", callback_data="boss_list"))
    builder.row(types.InlineKeyboardButton(text="💎 Новинки 1.4.5", callback_data="menu_145"))
    
    await message.answer(
        "👋 **Добро пожаловать в Terraria Guide v1.4.5!**\n\n"
        "Я помогу тебе пройти путь от медного кинжала до Мунлорда. Выбери раздел:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- СПИСОК БОССОВ ---
@dp.callback_query(F.data == "boss_list")
async def show_bosses(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    # Кнопки для конкретных боссов
    builder.row(types.InlineKeyboardButton(text="👁️ Глаз Ктулху", callback_data="info_eye_of_cthulhu"))
    builder.row(types.InlineKeyboardButton(text="🔥 Стена Плоти", callback_data="info_wall_of_flesh"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    
    await callback.message.edit_text(
        "⚔️ **Порядок прохождения боссов:**\n\n"
        "Выбери босса, чтобы получить детальный гайд, тактику и список экипировки:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О БОССЕ ---
@dp.callback_query(F.data.startswith("info_"))
async def boss_detail(callback: types.CallbackQuery):
    boss_key = callback.data.replace("info_", "")
    data = get_boss_data().get(boss_key)
    
    text = (
        f"{data['title']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📝 **Описание:** {data['desc']}\n\n"
        f"⚔️ **Тактика:**\n{data['tactics']}\n\n"
        f"🛡️ **Экипировка:**\n{data['gear']}\n\n"
        f"🏟️ **Арена:** {data['arena']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"✨ *Актуально для версии 1.4.5*"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⬅️ К списку боссов", callback_data="boss_list"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(callback: types.CallbackQuery):
    # Код возврата в главное меню (как в start)
    await cmd_start(callback.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
