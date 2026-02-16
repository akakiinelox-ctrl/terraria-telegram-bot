import os
import json
import logging
import asyncio
import random
import html  # Для безопасного вывода текста
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from groq import AsyncGroq  # Асинхронный клиент

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 599835907 

# Инициализация клиентов
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class SearchState(StatesGroup):
    wait_query = State()

class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

# ==========================================
# 🧠 МОЗГ: ГИД (GROQ AI + HTML)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: Переменная GROQ_API_KEY не настроена в Railway.")
        return

    system_prompt = (
        "Ты — Гид из игры Terraria. Ты эксперт. Твоя цель: помогать игрокам выжить. "
        "Отвечай максимально точно, подробно и вариативно. "
        "ВАЖНО: Используй ТОЛЬКО HTML теги (<b>, <i>, <code>). Не используй Markdown (* или _). "
        "Если спрашивают крафт — распиши его. Если прогрессию — дай пошаговый гайд."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
        )
        
        response = chat_completion.choices[0].message.content
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🤔 Спросить ещё", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"AI ERROR: {e}")
        # Если HTML поломался, отправляем чистый текст
        await message_to_edit.edit_text(f"🤯 <b>Гид:</b> Путник, мои мысли спутались. Попробуй ещё раз.\n\n<code>{html.escape(str(e)[:100])}</code>", parse_mode="HTML")

# --- ОБРАБОТЧИКИ ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_query)
    await callback.message.answer("👋 <b>Я слушаю, Террариец!</b>\n\nСпрашивай о чём угодно (крафты, боссы, советы по классам):", parse_mode="HTML")
    await callback.answer()

@dp.message(SearchState.wait_query)
async def chat_process(message: types.Message, state: FSMContext):
    sent_msg = await message.answer("🤔 <i>Гид вспоминает рецепты...</i>", parse_mode="HTML")
    await ask_guide_ai(sent_msg, message.text)
    await state.clear()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Задать вопрос Гиду", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await message.answer("🛠 <b>Terraria Tactical Assistant</b>\n\nЯ — твой Гид. Спрашивай меня о чём угодно!", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
