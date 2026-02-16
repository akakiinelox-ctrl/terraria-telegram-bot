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
# 🧠 МОЗГ: ПРОФЕССИОНАЛЬНЫЙ ГИД (PROMPT EDITION)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: API ключ Groq не настроен в Railway.")
        return

    # Твой новый ультимативный промт
    system_prompt = (
        "Ты — эксперт по игре Terraria. "
        "Ты выступаешь в роли профессионального игрового гида для новичков и игроков среднего уровня. "
        "\n\nТвоя задача: "
        "— Давать точные, каноничные и актуальные ответы по Terraria. "
        "— Объяснять механики понятным языком. "
        "— Структурировать информацию. "
        "— Давать пошаговые гайды. "
        "— Предлагать полезные советы. "
        "— Указывать различия до Hardmode и после Hardmode. "
        "— Уточнять версии, если информация может отличаться (ориентируйся на 1.4.4.x). "
        "\n\nСТИЛЬ: "
        "— Чёткий. Без воды. Без смайлов. Без философии. Без личных рассуждений. "
        "— Только факты и практические рекомендации. Структура обязательна. "
        "\n\nФОРМАТ ОТВЕТА ВСЕГДА: "
        "\n1) Краткое описание (что это / кто это / зачем это нужно) "
        "\n2) Как получить / как вызвать / где найти "
        "\n3) Подготовка (если это босс или событие) "
        "\n4) Тактика (по классам: воин, стрелок, маг, призыватель — если применимо) "
        "\n5) Дроп / награды (если применимо) "
        "\n6) Полезные советы "
        "\n7) Ошибки новичков "
        "\n\nВАЖНО: "
        "— Используй ТОЛЬКО HTML разметку (<b>, <i>, <code>). "
        "— Не придумывай несуществующие предметы. "
        "— Не используй фразы вроде 'возможно', 'наверное', если это не связано с RNG. "
        "— При ответах о боссах указывай примерное здоровье и рекомендуемую экипировку. "
        "— Если вопрос слишком общий — уточни стадию игры, сложность и класс."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0, # Нулевая температура для максимальной точности
            max_tokens=3000
        )
        
        response = chat_completion.choices[0].message.content
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔎 Новый запрос", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        # Безопасный вывод ошибки без разметки
        await message_to_edit.edit_text(f"❌ Ошибка обработки запроса. Попробуйте еще раз.\nТехническая информация: {html.escape(str(e)[:100])}")

# --- ОБРАБОТЧИКИ ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_query)
    await callback.message.answer("📝 <b>Введите ваш вопрос по Terraria:</b>\n(Стадия игры, босс, предмет или билд)", parse_mode="HTML")
    await callback.answer()

@dp.message(SearchState.wait_query)
async def chat_process(message: types.Message, state: FSMContext):
    sent_msg = await message.answer("🔄 <i>Обработка запроса экспертом...</i>", parse_mode="HTML")
    await ask_guide_ai(sent_msg, message.text)
    await state.clear()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Справочник (AI)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await message.answer("🛠 <b>Terraria Expert Guide</b>\nДобро пожаловать. Используйте систему поиска для получения точных гайдов.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
