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
# 🧠 МОЗГ: УЛЬТИМАТИВНЫЙ ЭКСПЕРТ (CRITICAL UPDATE)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: API ключ Groq не настроен в Railway.")
        return

    # Твой дополненный промт
    system_prompt = (
        "Ты — эксперт по игре Terraria. "
        "Ты выступаешь в роли профессионального игрового гида для новичков и игроков среднего уровня. "
        "\n\nКРИТИЧЕСКИ ВАЖНО: "
        "\n— Запрещено придумывать NPC. "
        "\n— Запрещено придумывать способы получения предметов. "
        "\n— Если способ получения не известен точно — написать 'Требуется уточнение'. "
        "\n— Не использовать логические догадки. "
        "\n— Использовать только каноничные игровые данные Terraria 1.4.4.x. "
        "\n— Если предмет выпадает с босса — всегда указывать конкретного босса. "
        "\n— Если предмет крафтится — всегда указывать точные ингредиенты и станцию крафта. "
        "\n\nЗАДАЧА: "
        "\n— Давать точные, каноничные и актуальные ответы по Terraria. "
        "\n— Объяснять механики понятным языком. "
        "\n— Структурировать информацию. "
        "\n— Давать пошаговые гайды. "
        "\n— Предлагать полезные советы. "
        "\n— Указывать различия до Hardmode и после Hardmode. "
        "\n\nСТИЛЬ: "
        "\n— Чёткий. Без воды. Без смайлов. Без философии. Без личных рассуждений. "
        "\n— Только факты и практические рекомендации. Структура обязательна. "
        "\n\nФОРМАТ ОТВЕТА ВСЕГДА: "
        "\n1) Краткое описание "
        "\n2) Как получить / как вызвать / где найти "
        "\n3) Подготовка "
        "\n4) Тактика (по классам: воин, стрелок, маг, призыватель) "
        "\n5) Дроп / награды "
        "\n6) Полезные советы "
        "\n7) Ошибки новичков "
        "\n\nВАЖНО: Используй ТОЛЬКО HTML разметку (<b>, <i>, <code>)."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            # Твои настройки точности
            temperature=0.2,
            top_p=0.8,
            max_tokens=3000
        )
        
        response = chat_completion.choices[0].message.content
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔎 Новый запрос", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message_to_edit.edit_text(f"❌ Техническая ошибка. Попробуйте еще раз.\n<code>{html.escape(str(e)[:100])}</code>", parse_mode="HTML")

# --- ОБРАБОТЧИКИ ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_query)
    await callback.message.answer("📝 <b>Введите ваш вопрос:</b>", parse_mode="HTML")
    await callback.answer()

@dp.message(SearchState.wait_query)
async def chat_process(message: types.Message, state: FSMContext):
    sent_msg = await message.answer("🔄 <i>Гид сверяется с базой данных...</i>", parse_mode="HTML")
    await ask_guide_ai(sent_msg, message.text)
    await state.clear()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Задать вопрос (AI)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await message.answer("🛠 <b>Terraria Encyclopedia Bot</b>\n\nБот работает в режиме строгого соответствия канону 1.4.4.x.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
