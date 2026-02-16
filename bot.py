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
# 🧠 МОЗГ: SMART WIKI RAG
# ==========================================

async def get_wiki_search_term(user_question):
    """
    Спрашивает у ИИ, как может называться статья на Вики для этого вопроса.
    Пример: Вопрос "Кто после пчелы?" -> Ответ ИИ "Боссы"
    """
    try:
        chat = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Ты — поисковый алгоритм Terraria Wiki. Твоя задача — превратить вопрос пользователя "
                        "в ТОЧНОЕ название статьи на Русской Terraria Wiki.\n"
                        "Примеры:\n"
                        "- 'Как сделать зенит?' -> 'Зенит'\n"
                        "- 'Кто идет после пчелы?' -> 'Боссы'\n"
                        "- 'Где найти крылья?' -> 'Крылья'\n"
                        "- 'Сет на мага' -> 'Класс'\n"
                        "В ОТВЕТЕ ПИШИ ТОЛЬКО ОДНО СЛОВО ИЛИ ФРАЗУ (НАЗВАНИЕ СТАТЬИ)."
                    )
                },
                {"role": "user", "content": user_question}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        return chat.choices[0].message.content.strip()
    except:
        return None

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

        # 2. Скачивание исходного кода
        async with session.get(api_url, params={
            "action": "query", "prop": "revisions", "rvprop": "content", 
            "titles": title, "format": "json"
        }) as resp:
            data = await resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid in pages:
                if pid == "-1": return None
                raw_text = pages[pid].get("revisions", [{}])[0].get("*", "")
                return {"title": title, "text": raw_text, "url": url}
    return None

async def generate_answer(user_query, wiki_data):
    """Генерирует ответ через Groq на основе Wikitext"""
    context_text = wiki_data['text'][:20000] # Берем много текста
    
    system_prompt = (
        "Ты — Гид из Terraria. Ответь на вопрос пользователя, используя ТОЛЬКО предоставленный код статьи Wiki."
        "\n\nПРАВИЛА:"
        "\n1. Если спрашивают порядок боссов, ищи списки в тексте."
        "\n2. Игнорируй технические теги, ищи суть."
        "\n3. Отвечай на русском языке, дружелюбно, используй эмодзи."
        "\n4. Если в статье нет ответа, честно скажи об этом."
    )

    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Статья Wiki: {wiki_data['title']}\nТекст: {context_text}\n\nВОПРОС: {user_query}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"Ошибка обработки: {e}"

# --- ОБРАБОТЧИКИ ПОИСКА ---

@dp.callback_query(F.data == "m_search")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer(
        "🔎 **Я слушаю тебя, Путник.**\n\n"
        "Спроси меня о чём угодно:\n"
        "• _Как скрафтить Зенит?_\n"
        "• _Какой босс после Пчелы?_\n"
        "• _Лучшая броня на воина?_"
    )
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def search_process(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    status_msg = await message.answer("🤔 *Пытаюсь понять твой вопрос...*")
    
    # ЭТАП 1: Пробуем найти статью напрямую
    wiki_data = await get_wiki_content(user_query)
    
    # ЭТАП 2: Если напрямую не нашли, просим ИИ подобрать статью
    if not wiki_data:
        ai_suggestion = await get_wiki_search_term(user_query)
        if ai_suggestion and ai_suggestion.lower() != user_query.lower():
            await status_msg.edit_text(f"📖 *Похоже, нам нужна статья «{ai_suggestion}»... Ищу её.*")
            wiki_data = await get_wiki_content(ai_suggestion)
    
    # Если всё равно ничего не нашли
    if not wiki_data:
        await status_msg.edit_text(
            f"❌ Я перерыл всю библиотеку, но не нашел ответа на вопрос: **{user_query}**.\n"
            "Попробуй переформулировать.",
            reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="m_search")).as_markup()
        )
        return

    # ЭТАП 3: Анализируем статью и отвечаем
    await status_msg.edit_text(f"🧠 *Изучаю свиток «{wiki_data['title']}»...*")
    ai_answer = await generate_answer(user_query, wiki_data)
    
    # Кнопки
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔗 Читать на Wiki", url=wiki_data['url']))
    builder.row(types.InlineKeyboardButton(text="🔎 Новый поиск", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    
    # Обрезаем если очень длинно
    if len(ai_answer) > 4000: ai_answer = ai_answer[:4000] + "..."

    await status_msg.edit_text(
        f"📚 **{wiki_data['title']}**\n\n{ai_answer}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.clear()


# ==========================================
# (ВСТАВЬ СЮДА ОСТАЛЬНОЙ КОД:
# RECIPES, CHECKLIST_DATA,
# Обработчики m_bosses, m_alchemy, m_npcs, m_calc, m_events и т.д.)
# ==========================================

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Умный поиск (Wiki)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет! Я подключен к нейросети и Wiki. Спроси меня о чем угодно (крафт, тактика, прогресс)."
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state=state)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
