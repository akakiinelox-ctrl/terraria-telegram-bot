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
# 🧠 МОЗГ: УЛЬТИМАТИВНЫЙ ГИД (ФИКС ГАЛЛЮЦИНАЦИЙ)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: API ключ не настроен.")
        return

    # МАКСИМАЛЬНО ЖЕСТКИЙ ПРОМТ ДЛЯ ТОЧНОСТИ
    system_prompt = (
        "Ты — база данных игры Terraria 1.4.4. Твоя задача — давать 100% достоверную информацию. "
        "ЗАПРЕЩЕНО: выдумывать предметы, путать боссов или условия активации событий. "
        "Если ты не уверен в ответе на 100%, напиши: 'Путник, даже я не помню этого, загляни в официальную Wiki'. "
        "\n\nПРАВИЛА ОФОРМЛЕНИЯ:"
        "\n- Используй ТОЛЬКО HTML (<b>, <i>, <code>, <u>)."
        "\n- Название предмета/босса всегда выделяй <b>жирным</b>."
        "\n- Рецепты пиши в формате: <code>Предмет + Предмет = Результат (Место)</code>."
        "\n- Всегда используй эмодзи для разделов."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            # ТЕМПЕРАТУРА 0.1 ДЕЛАЕТ ЕГО МАКСИМАЛЬНО ТОЧНЫМ
            temperature=0.1, 
            max_tokens=2048
        )
        
        response = chat_completion.choices[0].message.content
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔎 Спросить еще", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message_to_edit.edit_text("🤯 <b>Гид:</b> Мои архивы временно недоступны. Попробуй позже!")

# --- ОБРАБОТЧИКИ ЧАТА ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_query)
    await callback.message.answer("👋 <b>Спрашивай, Террариец!</b>\nЯ отвечу на любой вопрос о крафте, боссах или прогрессии мира.", parse_mode="HTML")
    await callback.answer()

@dp.message(SearchState.wait_query)
async def chat_process(message: types.Message, state: FSMContext):
    sent_msg = await message.answer("🤔 <i>Гид сверяется с картами...</i>", parse_mode="HTML")
    await ask_guide_ai(sent_msg, message.text)
    await state.clear()

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Задать вопрос Гиду", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    
    await message.answer("🛠 <b>Terraria Tactical Assistant</b>\nВыбери раздел или нажми на поиск, чтобы пообщаться со мной напрямую.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
