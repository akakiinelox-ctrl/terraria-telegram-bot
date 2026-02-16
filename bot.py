import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from groq import Groq

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 599835907

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

class SearchState(StatesGroup):
    wait_item_name = State()

# --- ФУНКЦИИ ЗАГРУЗКИ ДАННЫХ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def save_user(user_id, username, source="organic"):
    users = get_data('users')
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in users:
        users[user_id] = {"username": username, "join_date": today, "source": source, "last_active": today}
    else:
        users[user_id]["last_active"] = today
        users[user_id]["username"] = username
    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except: pass

# ==========================================
# 🧠 МОЗГ: WIKI (Raw Code) + ИИ
# ==========================================

async def get_wiki_content(query):
    """Ищет статью и скачивает её ИСХОДНЫЙ КОД (Wikitext)"""
    api_url = "https://terraria.wiki.gg/ru/api.php"
    async with aiohttp.ClientSession() as session:
        # 1. Поиск точного заголовка
        async with session.get(api_url, params={
            "action": "opensearch", "search": query, "limit": "1", "format": "json"
        }) as resp:
            data = await resp.json()
            if not data[1]: return None
            title = data[1][0]
            url = data[3][0]

        # 2. Скачивание исходного кода страницы (Revisions)
        # Это позволяет получить данные таблиц и шаблонов, которые пропадают в обычном extract
        async with session.get(api_url, params={
            "action": "query", 
            "prop": "revisions", 
            "rvprop": "content", # Запрашиваем контент
            "titles": title,
            "format": "json"
        }) as resp:
            data = await resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid in pages:
                if pid == "-1": return None # Страница не существует
                
                # Получаем сырой текст (wikitext)
                raw_text = pages[pid].get("revisions", [{}])[0].get("*", "")
                return {"title": title, "text": raw_text, "url": url}
    return None

async def generate_answer(query, wiki_data):
    """Генерирует ответ через Groq на основе Wikitext"""
    # Обрезаем текст, чтобы не перегрузить токенами, но берем побольше
    context_text = wiki_data['text'][:25000] 
    
    system_prompt = (
        "Ты — Гид из Terraria. Твоя задача — ответить на вопрос, анализируя ИСХОДНЫЙ КОД (Wikitext) статьи."
        "\n\nКАК ЧИТАТЬ ДАННЫЕ:"
        "\n- Рецепты находятся в блоках {{Рецепт|...}} или {{Recipe}}."
        "\n- Характеристики предмета находятся в {{ItemInfobox...}}."
        "\n- Дроп находится в таблицах {{Drop...}}."
        "\n\nПРАВИЛА:"
        "\n1. Игнорируй технический мусор, ищи суть."
        "\n2. Если спрашивают КРАФТ ЗЕНИТА: Найди дерево рецептов. Там много мечей. Перечисли их все."
        "\n3. Отвечай красиво, на русском языке, используй Markdown списки."
        "\n4. Не придумывай ничего, чего нет в коде статьи."
    )

    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Исходный код статьи Wiki: {context_text}\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2, # Низкая температура для точности фактов
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"Ошибка обработки данных: {e}"

# --- ОБРАБОТЧИКИ ПОИСКА ---

@dp.callback_query(F.data == "m_search")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer("🔎 **Введите название (предмет, босс, биом):**\nНапример: _Зенит, Плантера, Терра-меч_")
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def search_process(message: types.Message, state: FSMContext):
    query = message.text.strip()
    status_msg = await message.answer("🔄 *Подключаюсь к Wiki (скачиваю данные)...*")
    
    # 1. Качаем данные
    wiki_data = await get_wiki_content(query)
    
    if not wiki_data:
        await status_msg.edit_text(f"❌ Статья «{query}» не найдена на Wiki.\nПопробуйте написать точнее (например, не 'меч', а 'Зенит').")
        return

    # 2. Анализируем через ИИ
    await status_msg.edit_text(f"🧠 *Анализирую рецепты и таблицы для «{wiki_data['title']}»...*")
    ai_answer = await generate_answer(query, wiki_data)
    
    # 3. Выдаем результат
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔗 Читать на сайте", url=wiki_data['url']))
    builder.row(types.InlineKeyboardButton(text="🔎 Искать еще", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    
    # Обрезаем ответ, если он слишком длинный для Telegram (лимит 4096)
    if len(ai_answer) > 4000:
        ai_answer = ai_answer[:4000] + "...\n(Читать далее на сайте)"

    await status_msg.edit_text(
        f"📚 **{wiki_data['title']}**\n\n{ai_answer}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.clear()


# ==========================================
# (СЮДА ВСТАВЬ ОСТАЛЬНОЙ КОД: 
#  RECIPES, CHECKLIST_DATA, 
#  Обработчики m_bosses, m_alchemy, m_npcs, m_calc из предыдущих файлов)
# ==========================================

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Умный поиск (Wiki RAG)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    
    await message.answer("🛠 **Terraria Bot**\nЯ читаю Wiki за тебя! Спроси меня о крафте или боссе.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state=state)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
