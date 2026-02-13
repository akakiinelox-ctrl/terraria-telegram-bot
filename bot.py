import os
import logging
import asyncio
import random
import aiohttp
import html
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ" # <--- ВСТАВЬ ТОКЕН СЮДА

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА ГИДА (OPTIMIZED) ---
async def get_ai_guide_answer(user_text):
    url = "https://text.pollinations.ai/"
    
    # Строгая и короткая инструкция
    system_prompt = (
        "Ты — Гид из Terraria. Отвечай на русском. "
        "Твои ответы должны быть очень короткими (максимум 2 предложения). "
        "Давай только конкретные советы по игре. Без форматирования."
    )
    
    fallback_phrases = [
        "Я не уверен... Покажи мне Материал.",
        "Ночью выходить опасно.",
        "Слизни сегодня агрессивны.",
        "Я забыл этот рецепт."
    ]

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "model": "openai",
                "seed": random.randint(1, 9999)
            }
            
            # Таймаут 8 секунд
            async with asyncio.timeout(8):
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if not text or len(text) < 2 or "<" in text:
                            return random.choice(fallback_phrases)
                        return html.escape(text.strip())
                    return random.choice(fallback_phrases)

    except Exception as e:
        logging.error(f"AI Error: {e}")
        return random.choice(fallback_phrases)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🧔 **Я Гид.** Спрашивай, я помогу советом.", parse_mode="Markdown")

@dp.message()
async def chat_with_guide(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    answer = await get_ai_guide_answer(message.text)
    await message.answer(f"🧔 {answer}", parse_mode="HTML")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())