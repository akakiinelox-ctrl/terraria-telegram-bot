import os
import json
import logging
import asyncio
import random
import aiohttp
import html  # <--- ВАЖНО: Добавил библиотеку для безопасного текста
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
ADMIN_ID = 599835907  # Твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

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
            if not content:  # Если файл пустой
                return {}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

# --- АНАЛИТИКА: СОХРАНЕНИЕ ЮЗЕРА ---
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
# 🔍 ЛОГИКА ЖИВОГО ГАЙДА (Wiki API)
# ==========================================
async def get_wiki_guide(query):
    url = "https://terraria.wiki.gg/ru/api.php"
    search_params = {
        "action": "query", "list": "search", "srsearch": query,
        "format": "json", "srlimit": 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=search_params) as resp:
                if resp.status != 200: return None
                s_data = await resp.json()
                if not s_data.get('query', {}).get('search'): return None
                
                page_title = s_data['query']['search'][0]['title']
                
                txt_params = {
                    "action": "query", "prop": "extracts", "exintro": True,
                    "explaintext": True, "titles": page_title, "format": "json"
                }
                async with session.get(url, params=txt_params) as txt_resp:
                    t_data = await txt_resp.json()
                    pages = t_data['query']['pages']
                    page_id = list(pages.keys())[0]
                    return {
                        "title": page_title,
                        "text": pages[page_id].get('extract', 'Описание отсутствует.'),
                        "url": f"https://terraria.wiki.gg/ru/wiki/{page_title.replace(' ', '_')}"
                    }
    except Exception as e:
        logging.error(f"Ошибка Wiki API: {e}")
        return None

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ
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
    
    ref_source = command.args if command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск предмета / Гайд", callback_data="m_search"))
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
# 🔍 ОБРАБОТКА ПОИСКА (ИСПРАВЛЕННАЯ)
# ==========================================
@dp.callback_query(F.data == "m_search")
async def search_entry(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.edit_text(
        "🔎 **Введите название предмета или моба:**\n\nЯ найду информацию в базе знаний Terraria.", 
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")).as_markup(),
        parse_mode="Markdown"
    )

@dp.message(SearchState.waiting_for_query)
async def search_result(message: types.Message, state: FSMContext):
    # Показываем статус "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")
    
    res = await get_wiki_guide(message.text)
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Искать снова", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    
    if res:
        # Экранируем текст для безопасного HTML
        safe_title = html.escape(res['title'])
        safe_text = html.escape(res['text'])
        
        # Обрезаем слишком длинный текст
        if len(safe_text) > 1000:
            safe_text = safe_text[:1000] + "..."

        text_to_send = (
            f"📖 <b>Гайд: {safe_title}</b>\n\n"
            f"{safe_text}\n\n"
            f"🔗 <a href='{res['url']}'>Читать подробнее на Wiki</a>"
        )
        
        # Используем HTML, чтобы не ломалось из-за символов * или _
        await message.answer(text_to_send, reply_markup=builder.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer("❌ Ничего не найдено. Попробуйте другое название.", reply_markup=builder.as_markup())

# ==========================================
# ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ
# ==========================================

@dp.callback_query(F.data == "m_checklist")
async def checklist_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items():
        builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_cat:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🗺 **Карта прогресса Terraria**\n\nВыбери текущий этап приключения.", reply_markup=builder.as_markup())

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
    builder.row(types.InlineKeyboardButton(text="📊 Анализ", callback_data="chk_res"), types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    await message.edit_text(f"📋 **Этап: {CHECKLIST_DATA[cat]['name']}**\n┃ {bar} {perc}%\n┗━━━━━━━━━━━━━━\nНажимай на задачи, чтобы отметить их.", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("chk_tog:"))
async def toggle_item(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    data = await state.get_data()
    cat = data.get('current_cat')
    completed = data.get('completed', [])
    if index in completed: completed.remove(index)
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
    if count == total: res = "👑 **МАСТЕР ЭТАПА**\n\nТы полностью закрыл этот этап!"
    elif count >= total // 2: res = f"⚔️ **ОПЫТНЫЙ ВОИН ({count}/{total})**\n\nШансы высоки."
    else: res = f"💀 **СМЕРТНИК ({count}/{total})**\n\nТвоя подготовка ужасна."
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Продолжить", callback_data=f"chk_cat:{cat}"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"), types.InlineKeyboardButton(text="📜 Книга", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимическая лаборатория**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    for ing in ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]:
        builder.add(types.InlineKeyboardButton(text=ing, callback_data=f"ing:{ing}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Варить!", callback_data="alc_mix"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🌿 **Бросай ингредиенты (выбери 2):**", reply_markup=builder.as_markup())

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
        else: await callback.answer("Уже в котле!")
    else: await callback.answer("Котёл полон!")

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2: return await callback.answer("Нужно 2 ингредиента!")
    result = RECIPES.get(tuple(sorted(mix)), "💥 Ба-бах! Получилась бесполезная жижа...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Еще раз", callback_data="alc_craft"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(f"🧪 **Результат:**\n\n{result}", reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data == "alc_book")
async def alchemy_book(callback: types.CallbackQuery):
    data = get_data('alchemy').get('sets', {})
    builder = InlineKeyboardBuilder()
    for key, s in data.items(): builder.row(types.InlineKeyboardButton(text=s['name'], callback_data=f"alc_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text("📜 **Книга рецептов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("alc_s:"))
async def alchemy_set_details(callback: types.CallbackQuery):
    set_key = callback.data.split(":")[1]
    alc_set = get_data('alchemy')['sets'][set_key]
    text = f"🧪 **Сет: {alc_set['name']}**\n\n"
    for p in alc_set['potions']: text += f"🔹 {p['name']}\n└ {p['effect']}\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="alc_book"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    ch = random.choice([{"t": "🏹 Робин Гуд", "q": "Луки только!"}, {"t": "🧨 Подрывник", "q": "Взрывчатка!"}])
    text = f"🎲 **{ch['t']}**\n\n{ch['q']}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎲 Еще", callback_data="m_random"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="b_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("👹 **Категория:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("🎯 **Цель:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Эквип", callback_data=f"b_g:{st}:{k}"), types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"), types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    try: await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())
    except: 
        await callback.message.delete()
        await callback.message.answer(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    data = get_data('bosses')[st][k]
    txt = data.get(fld, "Данные обновляются...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    
    if fld == "arena" and "arena_img" in data and data["arena_img"]:
        await callback.message.delete()
        try: await callback.message.answer_photo(photo=data["arena_img"], caption=f"🏟️ **Схема Арены:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")
        except: await callback.message.answer(f"🏟️ **Схема Арены:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")
    else: await callback.message.edit_text(f"📝 **Информация:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for cid, name in {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🛡️ **Выберите класс:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(items): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("🎒 **Лучшие предметы:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    itm = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['craft']}", show_alert=True)

@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="ev_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="ev_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("📅 **События:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data('events')[stage]
    builder = InlineKeyboardBuilder()
    for key, ev in data.items(): builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 **Выбери:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data('events')[stage][key]
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text(f"⚔️ **{ev['name']}**\n\n📢 {ev['trigger']}\n🎁 {ev['drops']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Классы:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    for k, v in {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}.items():
        builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes"))
    await callback.message.edit_text("📅 **Этап:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_c:"))
async def class_cats(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"), types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"), types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}"))
    await callback.message.edit_text("Что смотрим?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    data = get_data('classes')[cid]['stages'][sid][cat]
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(data): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    await callback.message.edit_text("🎒 **Выбери предмет:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="📜 Список", callback_data="n_list"), types.InlineKeyboardButton(text="🏡 Советы", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("👥 **NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **NPC:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list"))
    await callback.message.edit_text(f"👤 **{npc['name']}**\n📍 {npc['biome']}\n❤️ {npc['loves']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("🏡 Счастье влияет на цены!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_fishing")
async def fishing_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🐠 Квесты", callback_data="fish_list"), types.InlineKeyboardButton(text="📦 Ящики", callback_data="fish_crates"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🎣 **Рыбалка**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_list")
async def fish_biomes(callback: types.CallbackQuery):
    data = get_data('fishing').get('quests', {})
    builder = InlineKeyboardBuilder()
    for biome in data.keys(): builder.add(types.InlineKeyboardButton(text=biome, callback_data=f"fish_q:{biome}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 **Биом:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fish_q:"))
async def fish_biome_info(callback: types.CallbackQuery):
    biome = callback.data.split(":")[1]
    data = get_data('fishing').get('quests', {}).get(biome, [])
    text = f"📍 **{biome}**\n"
    for f in data: text += f"🐟 {f['name']}\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_list"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_crates")
async def fish_crates(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📦 Ящики содержат руду и аксессуары!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🛡️ Сеты", callback_data="calc_armor"), types.InlineKeyboardButton(text="⛏️ Руда", callback_data="calc_ores"))
    builder.row(types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Калькулятор**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_armor")
async def calc_armor_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for n, c in {"Железо": 75, "Золото": 90, "Святой": 54}.items(): builder.row(types.InlineKeyboardButton(text=f"{n} ({c})", callback_data=f"do_arm_c:{n}:{c}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ **Выбери сет:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("do_arm_c:"))
async def do_armor_calc(callback: types.CallbackQuery):
    _, name, bars = callback.data.split(":")
    total = int(bars) * (3 if "Железо" in name else 4)
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calc_armor"))
    await callback.message.edit_text(f"🛡️ **{name}**: Нужно {total} руды.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Медь (3:1)", callback_data="ore_sel:3"), types.InlineKeyboardButton(text="Золото (4:1)", callback_data="ore_sel:4"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ **Металл:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ore_sel:"))
async def ore_input_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_ratio=callback.data.split(":")[1])
    await state.set_state(CalcState.wait_ore_count)
    await callback.message.answer("🔢 Слитков:")

@dp.message(CalcState.wait_ore_count)
async def ore_input_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        t = int(message.text) * int(data['current_ratio'])
        await message.answer(f"⛏ Нужно {t} руды.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Число!")

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 Цена:")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        await message.answer(f"💰 Скидка: {round(p*0.83, 2)}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Число!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
