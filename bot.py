import os
import json
import logging
import asyncio
import html
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from groq import AsyncGroq 

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
bot = Bot(token=TOKEN)
dp = Dispatcher()

class SearchState(StatesGroup):
    wait_query = State()

# ==========================================
# 🧠 МОЗГ: БЕЗОШИБОЧНЫЙ ГИД (ФИКС ВСЕХ ОШИБОК)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: API ключ Groq не настроен.")
        return

    # МАКСИМАЛЬНО СТРОГИЙ ПРОМТ
    system_prompt = (
        "Ты — официальный Гид из Terraria 1.4.4. Твоя задача — давать ИСКЛЮЧИТЕЛЬНО точные ответы. "
        "Если ты не знаешь ответа или сомневаешься — не выдумывай, а отправь игрока на Wiki. "
        "\n\nЖЕСТКИЕ ПРАВИЛА:"
        "\n1. ХАРДМОД: Активируется ТОЛЬКО после убийства Стены Плоти (Wall of Flesh). Никаких исключений."
        "\n2. БОССЫ: Не выдумывай новых боссов. Используй только тех, что есть в игре."
        "\n3. КРАФТ: Пиши точные ингредиенты. Если это сложный предмет (Зенит, Сапоги терра-искры), распиши все компоненты."
        "\n4. СТИЛЬ: Используй HTML-разметку (<b>, <i>, <code>). Запрещено использовать Markdown."
        "\n5. Тон: Дружелюбный, профессиональный, экспертный."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            # ТЕМПЕРАТУРА 0 — ЭТО РЕЖИМ СТРОГОГО ФАКТА
            temperature=0, 
            max_tokens=2048
        )
        
        response = chat_completion.choices[0].message.content
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔎 Спросить еще", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message_to_edit.edit_text("🤯 <b>Гид:</b> Мои свитки сгорели! Попробуй задать вопрос позже.")

# --- ОБРАБОТЧИКИ ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_query)
    await callback.message.answer("👋 <b>Слушаю тебя, Террариец!</b>\nЯ отвечу на любой вопрос о мире игры. Что тебя интересует?", parse_mode="HTML")
    await callback.answer()

@dp.message(SearchState.wait_query)
async def chat_process(message: types.Message, state: FSMContext):
    sent_msg = await message.answer("🤔 <i>Гид сверяется с древними записями...</i>", parse_mode="HTML")
    await ask_guide_ai(sent_msg, message.text)
    await state.clear()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Задать вопрос Гиду", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await message.answer("🛠 <b>Terraria Tactical Assistant</b>\nЗадавай вопросы или выбирай разделы ниже.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
