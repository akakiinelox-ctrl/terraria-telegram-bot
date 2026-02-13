import os
import json
import logging
import asyncio
import random
import aiohttp
import html
# --- НОВЫЙ ИМПОРТ ДЛЯ GEMINI ---
import google.generativeai as genai 
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТЕЛЕГРАМ_ТОКЕН_ЗДЕСЬ"
ADMIN_ID = 599835907  

# --- НАСТРОЙКИ GEMINI ---
# Вставь сюда ключ, который получишь в Google AI Studio
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDC5DhxG5FBr1WSmVnUJT59BEHtUYE3LLQ"

# Настраиваем модель
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Быстрая и легкая модель
    system_instruction="Ты — Гид из игры Terraria. Твоя задача — давать четкие, короткие и полезные советы игрокам на русском языке. Используй игровую терминологию. Не используй Markdown форматирование (жирный шрифт, курсив), пиши обычным текстом."
)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

class AIState(StatesGroup): 
    waiting_for_question = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

# --- ДАННЫЕ ДЛЯ АЛХИМИИ ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

# --- ДАННЫЕ ЧЕК-ЛИСТА ---
CHECKLIST_DATA = {
    "start": {
        "name": "🌱 Начало (Pre-Boss)",
        "items": [
            ("🏠 Деревня", "Построено 5+ домов и заселен Гид и Торговец."),
            ("❤️ Жизнь", "Найдено минимум 5 Кристаллов жизни."),
            ("💎 Броня", "Сет из драгоценных камней или Золота/Платины."),
            ("🔗 Мобильность", "Есть крюк-кошка и любые сапоги на бег."),
            ("⛏️ Инструменты", "Кирка способна копать Метеорит/Демонит.")
        ]
    },
    "pre_hm": {
        "name": "🌋 Финал Pre-HM",
        "items": [
            ("⚔️ Грань Ночи", "Или топовое оружие твоего класса."),
            ("❤️ 400 HP", "Здоровье на максимуме для этого этапа."),
            ("🌋 Адская трасса", "Дорожка в аду длиной минимум в 1500 блоков."),
            ("🌳 Карантин", "Туннели вокруг порчи/кримзона и дома."),
            ("🎒 Аксессуары", "Аксессуары перекованы на +4 защиты или урона.")
        ]
    },
    "hardmode_start": {
        "name": "⚙️ Ранний Хардмод",
        "items": [
            ("⚒️ Кузня", "Разрушено 3+ алтаря, есть мифриловая наковальня."),
            ("🧚 Крылья", "Выбиты первые крылья или куплены у Шамана."),
            ("🍏 500 HP", "Найдены фрукты жизни в джунглях."),
            ("🛡️ Титан", "Скрафчена броня из Титана или Адамантита."),
            ("🔑 Ферма", "Выбита или скрафчена Ключ-форма/Световой ключ.")
        ]
    },
    "endgame": {
        "name": "🌙 Финал (Мунлорд)",
        "items": [
            ("🛸 Транспорт", "Получен бесконечный полет (НЛО или Метла)."),
            ("🔫 Лунные башни", "Создано оружие из небесных фрагментов."),
            ("🩺 Реген-станция", "Арена с медом, лампами и статуями на HP."),
            ("🏆 Эндгейм сет", "Броня Жука, Спектральная или Тики/Шroomite.")
        ]
    }
}

# --- ЗАГРУЗКА ДАННЫХ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

# --- СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ (АНАЛИТИКА) ---
def save_user(user_id, username, source="organic"):
    users = get_data('users')
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "join_date": today,
            "source": source,
            "last_active": today,
            "activity_count": 1
        }
    else:
        users[user_id]["last_active"] = today
        users[user_id]["activity_count"] = users[user_id].get("activity_count", 0) + 1
        users[user_id]["username"] = username

    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Ошибка сохранения юзера: {e}")

# ==========================================
# 🧠 ЛОГИКА ИИ (GEMINI)
# ==========================================
async def get_ai_guide_answer(user_text):
    if not GEMINI_API_KEY or "ТВОЙ_КЛЮЧ" in GEMINI_API_KEY:
        return "Мой создатель забыл дать мне ключ от разума (API KEY). Скажи ему об этом!"

    try:
        # Отправляем запрос в Google Gemini (асинхронно)
        response = await model.generate_content_async(user_text)
        
        # Получаем текст ответа
        text = response.text
        
        # Очищаем и форматируем для HTML
        return html.escape(text.strip())
        
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return "Что-то помешало мне сосредоточиться... Спроси позже или переформулируй вопрос."

# --- ПОИСК WIKI (Оставлен как запасной вариант или для кнопки) ---
async def get_wiki_guide(query):
    url = "https://terraria.wiki.gg/ru/api.php"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1}) as resp:
            s_data = await resp.json()
            if not s_data.get('query', {}).get('search'): return None
            title = s_data['query']['search'][0]['title']
            async with session.get(url, params={"action": "query", "prop": "extracts", "exintro": True, "explaintext": True, "titles": title, "format": "json"}) as txt_resp:
                t_data = await txt_resp.json()
                page = next(iter(t_data['query']['pages'].values()))
                return {"title": title, "text": page.get('extract', ' Описание отсутствует.'), "url": f"https://terraria.wiki.gg/ru/wiki/{title.replace(' ', '_')}"}

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ (СТАТИСТИКА)
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 

    users = get_data('users')
    total = len(users)
    sources = {}
    active_today = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    for u in users.values():
        src = u.get("source", "organic")
        sources[src] = sources.get(src, 0) + 1
        if u.get("last_active") == today_str:
            active_today += 1

    text = (f"📊 **Статистика Бота:**\n\n"
            f"👥 Всего людей: **{total}**\n"
            f"🔥 Активны сегодня: **{active_today}**\n\n"
            f"📢 **Источники:**\n")
    for src, count in sources.items():
        text += f"• {src}: {count}\n"

    await message.answer(text, parse_mode="Markdown")

# ==========================================
# 🔗 ГЕНЕРАТОР РЕФЕРАЛЬНЫХ ССЫЛОК
# ==========================================
@dp.message(Command("link"))
async def generate_ref_link(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return

    if not command.args:
        await message.answer("❌ Пиши так: `/link tiktok`", parse_mode="Markdown")
        return

    bot_user = await bot.get_me()
    ref_name = command.args.strip()
    link = f"https://t.me/{bot_user.username}?start={ref_name}"
    
    await message.answer(f"✅ **Ссылка для {ref_name}:**\n\n`{link}`", parse_mode="Markdown")

# ==========================================
# 🛠 ТЕХНИЧЕСКАЯ ФУНКЦИЯ (ПОЛУЧЕНИЕ ID ФОТО/ВИДЕО)
# ==========================================
@dp.message(F.photo)
async def get_photo_id(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer(f"🖼 **ID фото:**\n\n`{message.photo[-1].file_id}`", parse_mode="Markdown")

@dp.message(F.video)
async def get_video_id(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer(f"📹 **ID видео:**\n\n`{message.video.file_id}`", parse_mode="Markdown")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext = None):
    if state: await state.clear()
    
    # --- ТРЕКИНГ ---
    ref_source = command.args if command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)
    # ---------------

    builder = InlineKeyboardBuilder()
    
    # КНОПКА ГИДА (GEMINI)
    builder.row(types.InlineKeyboardButton(text="🧔 Спросить Гида (AI)", callback_data="m_ai"))
    # Кнопка обычного поиска
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск (Wiki)", callback_data="m_search"))
    
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я помогу тебе подготовиться к любой угрозе. Выбери раздел:"
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    save_user(callback.from_user.id, callback.from_user.username)
    await cmd_start(callback.message, CommandObject(prefix="/", command="start", args=None), state)

# ==========================================
# 🗣 ДИАЛОГ С ГИДОМ (GEMINI AI)
# ==========================================
@dp.callback_query(F.data == "m_ai")
async def ai_entry(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AIState.waiting_for_question)
    await callback.message.edit_text(
        "🧔 <b>Гид слушает тебя.</b>\n\nСпроси меня о чем угодно: как убить босса, где найти руду или как скрафтить меч. Я постараюсь дать точный совет.\n\n"
        "✍️ <i>Напиши свой вопрос в чат:</i>",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")).as_markup(),
        parse_mode="HTML"
    )

@dp.message(AIState.waiting_for_question)
async def ai_response(message: types.Message, state: FSMContext):
    # Показываем, что бот печатает
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем ответ от GEMINI
    answer = await get_ai_guide_answer(message.text)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❓ Задать еще вопрос", callback_data="m_ai"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    
    # Ответ уже экранирован в функции, можно слать в HTML
    await message.answer(f"🧔 <b>Гид:</b>\n\n{answer}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

# ==========================================
# 🔍 ПОИСК (Wiki) - ОСТАВИЛ КАК ЗАПАСНОЙ ВАРИАНТ
# ==========================================
@dp.callback_query(F.data == "m_search")
async def search_entry(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.edit_text("🔎 <b>Введите название предмета:</b>", 
                                     reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.message(SearchState.waiting_for_query)
async def search_result(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, "typing")
    res = await get_wiki_guide(message.text)
    await state.clear()
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔍 Искать снова", callback_data="m_search")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    if res:
        safe_text = html.escape(res['text'])[:1000] + "..." if len(res['text']) > 1000 else html.escape(res['text'])
        await message.answer(f"📖 <b>Гайд: {html.escape(res['title'])}</b>\n\n{safe_text}\n\n🔗 <a href='{res['url']}'>Читать на Wiki</a>", 
                             reply_markup=builder.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
    else: await message.answer("❌ Ничего не найдено.", reply_markup=builder.as_markup())

# ==========================================
# 📋 РАЗДЕЛ: МАСШТАБНЫЙ ЧЕК-ЛИСТ
# ==========================================
@dp.callback_query(F.data == "m_checklist")
async def checklist_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items():
        builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_cat:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    
    await callback.message.edit_text(
        "🗺 **Карта прогресса Terraria**\n\nВыбери текущий этап приключения. Я помогу не упустить важные детали!",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("chk_cat:"))
async def checklist_start(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    await state.update_data(current_cat=cat, completed=[])
    await show_checklist(callback.message, cat, [])

async def show_checklist(message: types.Message, cat, completed_indices):
    builder = InlineKeyboardBuilder()
    items = CHECKLIST_DATA[cat]['items']
    
    total = len(items)
    done = len(completed_indices)
    perc = int((done / total) * 100)
    bar = "🟩" * done + "⬜" * (total - done)
    
    for i, (name, _) in enumerate(items):
        status = "✅" if i in completed_indices else "⭕"
        builder.row(types.InlineKeyboardButton(text=f"{status} {name}", callback_data=f"chk_tog:{i}"))
    
    builder.row(types.InlineKeyboardButton(text="📊 Анализ готовности", callback_data="chk_res"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    
    text = (
        f"📋 **Этап: {CHECKLIST_DATA[cat]['name']}**\n"
        f"┃ {bar} {perc}%\n"
        f"┗━━━━━━━━━━━━━━\n"
        f"Нажимай на задачи, чтобы отметить их как выполненные."
    )
    await message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("chk_tog:"))
async def toggle_item(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    data = await state.get_data()
    cat = data.get('current_cat')
    completed = data.get('completed', [])
    
    if index in completed:
        completed.remove(index)
    else:
        completed.append(index)
        await callback.answer(f"💡 {CHECKLIST_DATA[cat]['items'][index][1]}", show_alert=True)
    
    await state.update_data(completed=completed)
    await show_checklist(callback.message, cat, completed)

@dp.callback_query(F.data == "chk_res")
async def checklist_result(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat = data.get('current_cat')
    count = len(data.get('completed', []))
    total = len(CHECKLIST_DATA[cat]['items'])
    
    if count == total:
        res = "👑 **МАСТЕР ЭТАПА**\n\nТы полностью закрыл этот этап! Твоя подготовка идеальна."
    elif count >= total // 2:
        res = f"⚔️ **ОПЫТНЫЙ ВОИН ({count}/{total})**\n\nШансы высоки, но можно подготовиться лучше."
    else:
        res = f"💀 **СМЕРТНИК ({count}/{total})**\n\nТвоя подготовка ужасна. Тебя ждет быстрая смерть!"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Продолжить", callback_data=f"chk_cat:{cat}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

# ==========================================
# 🧪 РАЗДЕЛ: АЛХИМИЯ
# ==========================================
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить зелье", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="📜 Книга рецептов", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(
        "✨ **Алхимическая лаборатория**\n\nЗдесь ты можешь испытать удачу в варке или изучить готовые наборы для боя.",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    
    builder = InlineKeyboardBuilder()
    ingredients = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for ing in ingredients:
        builder.add(types.InlineKeyboardButton(text=ing, callback_data=f"ing:{ing}"))
    
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🔥 Начать варку!", callback_data="alc_mix"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    
    await callback.message.edit_text("🌿 **Бросай ингредиенты в котёл (выбери 2):**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ingredient(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    
    if len(mix) < 2:
        if ing not in mix:
            mix.append(ing)
            await state.update_data(mix=mix)
            await callback.answer(f"Добавлено: {ing}")
        else:
            await callback.answer("Этот ингредиент уже в котле!", show_alert=True)
    else:
        await callback.answer("Котёл полон!", show_alert=True)

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    
    if len(mix) < 2:
        await callback.answer("Нужно минимум 2 ингредиента!", show_alert=True)
        return

    mix_tuple = tuple(sorted(mix))
    result = RECIPES.get(mix_tuple, "💥 Ба-бах! Получилась бесполезная жижа...")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Сварить еще", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    
    await callback.message.edit_text(f"🧪 **Результат варки:**\n\n{result}", reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data == "alc_book")
async def alchemy_book(callback: types.CallbackQuery):
    data = get_data('alchemy').get('sets', {})
    builder = InlineKeyboardBuilder()
    for key, s in data.items():
        builder.row(types.InlineKeyboardButton(text=s['name'], callback_data=f"alc_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text("📜 **Книга проверенных рецептов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("alc_s:"))
async def alchemy_set_details(callback: types.CallbackQuery):
    set_key = callback.data.split(":")[1]
    alc_set = get_data('alchemy')['sets'][set_key]
    text = f"🧪 **Сет: {alc_set['name']}**\n━━━━━━━━━━━━━━\n\n"
    for p in alc_set['potions']:
        text += f"🔹 **{p['name']}**\n└ ✨ Эффект: {p['effect']}\n└ 🛠 Рецепт: {p['recipe']}\n\n"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 🎲 РАНДОМАЙЗЕР
# ==========================================
@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    challenges = [
        {"title": "🏹 Путь Робин Гуда", "rules": "• Только деревянные луки.\n• Природная броня.", "quest": "🎯 Победить Скелетрона обычными стрелами."},
        {"title": "🧨 Подрывник", "rules": "• Урон только взрывчаткой.", "quest": "🎯 Уничтожить Пожирателя Миров гранатами."},
        {"title": "⚔️ Истинный Рыцарь", "rules": "• Мечи без снарядов.", "quest": "🎯 Убить Короля Слизней вплотную."}
    ]
    res = random.choice(challenges)
    text = f"🎲 **Челлендж: {res['title']}**\n\n⚙️ **Правила:**\n{res['rules']}\n\n{res['quest']}"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎲 Другой челлендж", callback_data="m_random"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 👾 РАЗДЕЛ: БОССЫ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите категорию боссов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("🎯 **Выберите цель:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{st}:{k}"),
                types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"),
                types.InlineKeyboardButton(text="🏟️ Арена (Схема)", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    try: await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")
    except: 
        await callback.message.delete()
        await callback.message.answer(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    data = get_data('bosses')[st][k]
    txt = data.get(fld, "Данные обновляются...")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к боссу", callback_data=f"b_s:{st}:{k}"))
    
    if fld == "arena" and "arena_img" in data and data["arena_img"]:
        await callback.message.delete()
        try: await callback.message.answer_photo(photo=data["arena_img"], caption=f"🏟️ **Схема Арены:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")
        except: await callback.message.answer(f"🏟️ **Схема Арены:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")
    else: await callback.message.edit_text(f"📝 **Информация:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    clss = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for cid, name in clss.items(): builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🛡️ **Выберите свой класс:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items): builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("🎒 **Лучшие предметы для этого боя:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    item = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {item['name']}\n{item['craft']}", show_alert=True)

# ==========================================
# ⚔️ РАЗДЕЛ: СОБЫТИЯ
# ==========================================
@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="ev_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="ev_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("📅 **Выберите этап для просмотра нашествий:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data('events')[stage]
    builder = InlineKeyboardBuilder()
    for key, ev in data.items(): builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 **Выберите событие для тактического разбора:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data('events')[stage][key]
    text = (f"⚔️ **{ev['name']}**\n━━━━━━━━━━━━━━\n🔥 **Сложность:** {ev.get('difficulty', '???')}\n"
            f"💰 **Профит:** {ev.get('profit', '???')}\n\n📢 **Триггер:** {ev['trigger']}\n"
            f"🌊 **Волны:** {ev['waves']}\n🎁 **Дроп:** {ev['drops']}\n\n🛠 **ТАКТИКА:** \n_{ev.get('arena_tip', 'Стандартная арена.')}_")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 🛡️ РАЗДЕЛ: КЛАССЫ
# ==========================================
@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Выберите класс для изучения билда:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    sts = {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}
    for k, v in sts.items(): builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes"))
    await callback.message.edit_text("📅 **Выберите этап прохождения:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_c:"))
async def class_cats(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"),
                types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}"))
    await callback.message.edit_text("Что будем смотреть?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    data = get_data('classes')[cid]['stages'][sid][cat]
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(data): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    await callback.message.edit_text("🎒 **Выбери предмет для инфо:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

# ==========================================
# 👥 РАЗДЕЛ: NPC
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"),
                types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Выберите NPC:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = (f"👤 **{npc['name']}**\n━━━━━━━━━━━━━━\n📥 **Приход:** {npc.get('arrival', 'Стандарт')}\n"
           f"📍 **Биом:** {npc['biome']}\n🎁 **Бонус:** {npc.get('bonus', 'Нет')}\n\n"
           f"❤️ **Любит:** {npc['loves']}\n😊 **Нравится:** {npc['likes']}\n")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 **Советы по расселению:**\n1. Не более 3 NPC рядом.\n2. Счастье влияет на цены.\n3. Пилоны продаются только у счастливых NPC!"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# ==========================================
# 🎣 РАЗДЕЛ: РЫБАЛКА
# ==========================================
@dp.callback_query(F.data == "m_fishing")
async def fishing_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🐠 Квестовая рыба", callback_data="fish_list"),
                types.InlineKeyboardButton(text="📦 Ящики", callback_data="fish_crates"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🎣 **Справочник Рыболова**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_list")
async def fish_biomes(callback: types.CallbackQuery):
    data = get_data('fishing').get('quests', {})
    builder = InlineKeyboardBuilder()
    for biome in data.keys(): builder.add(types.InlineKeyboardButton(text=biome, callback_data=f"fish_q:{biome}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 **Выбери биом:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fish_q:"))
async def fish_biome_info(callback: types.CallbackQuery):
    biome = callback.data.split(":")[1]
    data = get_data('fishing').get('quests', {}).get(biome, [])
    text = f"📍 **Биом: {biome}**\n━━━━━━━━━━━━━━\n"
    for fish in data: text += f"🐟 **{fish['name']}**\n└ 💡 {fish['info']}\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_list"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_crates")
async def fish_crates(callback: types.CallbackQuery):
    data = get_data('fishing').get('crates', [])
    text = "📦 **Рыболовные ящики:**\n━━━━━━━━━━━━━━\n"
    for crate in data: text += f"{crate['name']}\n└ 🎁 Лут: {crate['drop']}\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# ==========================================
# 🧮 РАЗДЕЛ: КАЛЬКУЛЯТОР
# ==========================================
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы на Сет", callback_data="calc_armor"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Слитки ➔ Руда", callback_data="calc_ores"))
    builder.row(types.InlineKeyboardButton(text="💰 Скидки Гоблина", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Инженерный отдел**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_armor")
async def calc_armor_menu(callback: types.CallbackQuery):
    sets = {"Железо/Свинец": 75, "Золото/Платина": 90, "Святой сет": 54, "Хлорофит": 54}
    builder = InlineKeyboardBuilder()
    for name, count in sets.items(): builder.row(types.InlineKeyboardButton(text=f"{name} ({count} бар)", callback_data=f"do_arm_c:{name}:{count}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ **Выберите сет:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("do_arm_c:"))
async def do_armor_calc(callback: types.CallbackQuery):
    _, name, bars = callback.data.split(":")
    mult = 3 if "Железо" in name else 4
    total_ore = int(bars) * mult
    text = f"🛡️ **Комплект: {name}**\n━━━━━━━━━━━━━━\n📦 Слитков: {bars}\n⛏️ Руды: **{total_ore} шт.**"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calc_armor"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    ores = {"Медь (3:1)": 3, "Золото (4:1)": 4, "Адамантит (5:1)": 5}
    builder = InlineKeyboardBuilder()
    for name, ratio in ores.items(): builder.row(types.InlineKeyboardButton(text=name, callback_data=f"ore_sel:{ratio}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ **Выбери металл:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ore_sel:"))
async def ore_input_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_ratio=callback.data.split(":")[1])
    await state.set_state(CalcState.wait_ore_count)
    await callback.message.answer("🔢 **Введите количество слитков:**")

@dp.message(CalcState.wait_ore_count)
async def ore_input_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        total = int(message.text) * int(data['current_ratio'])
        await message.answer(f"⛏ Для **{message.text}** слитков нужно **{total}** руды.", 
                             reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К калькулятору", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите целое число!")

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 **Введите цену перековки (в золоте):**")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        text = (f"💰 **Для {price} золота:**\n\n😐 База: {price}\n😊 Скидка (17%): {round(price*0.83, 2)}\n❤️ Макс (33%): {round(price*0.67, 2)}")
        await message.answer(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К калькулятору", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())