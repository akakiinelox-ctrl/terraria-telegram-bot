import os
import json
import logging
import asyncio
import random
import aiohttp  # Библиотека для запросов к Wiki
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
ADMIN_ID = 599835907  

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

# --- ДАННЫЕ ДЛЯ АЛХИМИИ ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

# --- ДАННЫЕ ЧЕК-ЛИСТА (Оставлены без изменений) ---
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
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

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
# 🌐 WIKI API INTEGRATION
# ==========================================

async def get_wiki_data(query_text):
    """
    Делает запрос к API Terraria Wiki (wiki.gg)
    Возвращает: (Заголовок, Описание, Ссылка на картинку, Ссылка на статью)
    """
    api_url = "https://terraria.wiki.gg/ru/api.php"
    
    async with aiohttp.ClientSession() as session:
        # 1. Поиск точного названия статьи (Opensearch)
        search_params = {
            "action": "opensearch",
            "search": query_text,
            "limit": "1",
            "format": "json"
        }
        async with session.get(api_url, params=search_params) as resp:
            if resp.status != 200: return None
            data = await resp.json()
            
            # data[1] - заголовки, data[3] - ссылки
            if not data[1]: return None
            
            title = data[1][0]
            url = data[3][0]

        # 2. Получение контента (Текст + Картинка)
        content_params = {
            "action": "query",
            "prop": "extracts|pageimages",
            "titles": title,
            "pithumbsize": "500", # Размер картинки
            "exintro": "true",    # Только введение
            "explaintext": "true", # Убрать HTML теги
            "format": "json"
        }
        async with session.get(api_url, params=content_params) as resp:
            if resp.status != 200: return (title, "Ошибка получения данных.", None, url)
            c_data = await resp.json()
            
            pages = c_data.get("query", {}).get("pages", {})
            for page_id in pages:
                page = pages[page_id]
                extract = page.get("extract", "Описание отсутствует.")
                # Обрезаем слишком длинный текст
                if len(extract) > 800:
                    extract = extract[:800] + "..."
                
                thumbnail = page.get("thumbnail", {}).get("source")
                return (title, extract, thumbnail, url)
            
    return None

@dp.callback_query(F.data == "m_search")
async def wiki_search_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer("🔎 **Поиск по Wiki:**\n\nВведите название предмета, моба или биома (например: _Зенит, Плантера, Ад_).")
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def wiki_search_result(message: types.Message, state: FSMContext):
    query = message.text.strip()
    sent_msg = await message.answer("🔄 *Ищу в архивах Wiki...*")
    
    result = await get_wiki_data(query)
    
    if result:
        title, extract, image_url, page_url = result
        
        # Формируем кнопку
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📖 Читать полностью на Wiki", url=page_url))
        builder.row(types.InlineKeyboardButton(text="🔎 Искать ещё", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        caption = f"📚 **{title}**\n\n{extract}"
        
        await sent_msg.delete() # Удаляем сообщение "Ищу..."
        
        if image_url:
            await message.answer_photo(photo=image_url, caption=caption, reply_markup=builder.as_markup(), parse_mode="Markdown")
        else:
            await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await sent_msg.edit_text(
            f"❌ Ничего не найдено по запросу **{query}**.\nПопробуйте написать название точнее.",
            reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="m_search")).as_markup()
        )
    
    await state.clear()

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 
    users = get_data('users')
    total, active_today, today_str = len(users), 0, datetime.now().strftime("%Y-%m-%d")
    for u in users.values():
        if u.get("last_active") == today_str: active_today += 1
    await message.answer(f"📊 **Всего:** {total}\n🔥 **Сегодня:** {active_today}", parse_mode="Markdown")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref_source = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔎 Поиск (Wiki)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я помогу тебе. Выбери раздел:"
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state=state)

# ==========================================
# 📋 ОСТАЛЬНЫЕ РАЗДЕЛЫ
# ==========================================

@dp.callback_query(F.data == "m_checklist")
async def checklist_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items():
        builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_cat:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🗺 **Карта прогресса Terraria**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("chk_cat:"))
async def checklist_start(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    await state.update_data(current_cat=cat, completed=[])
    await show_checklist(callback.message, cat, [])

async def show_checklist(message: types.Message, cat, completed_indices):
    builder = InlineKeyboardBuilder()
    items = CHECKLIST_DATA[cat]['items']
    for i, (name, _) in enumerate(items):
        status = "✅" if i in completed_indices else "⭕"
        builder.row(types.InlineKeyboardButton(text=f"{status} {name}", callback_data=f"chk_tog:{i}"))
    builder.row(types.InlineKeyboardButton(text="📊 Анализ", callback_data="chk_res"),
                types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    await message.edit_text(f"📋 **Этап: {CHECKLIST_DATA[cat]['name']}**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("chk_tog:"))
async def toggle_item(callback: types.CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    cat, comp = data.get('current_cat'), data.get('completed', [])
    if idx in comp: comp.remove(idx)
    else: comp.append(idx); await callback.answer(f"💡 {CHECKLIST_DATA[cat]['items'][idx][1]}", show_alert=True)
    await state.update_data(completed=comp); await show_checklist(callback.message, cat, comp)

@dp.callback_query(F.data == "chk_res")
async def checklist_result(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat, count = data.get('current_cat'), len(data.get('completed', []))
    total = len(CHECKLIST_DATA[cat]['items'])
    res = f"⚔️ Результат: {count}/{total}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"),
                types.InlineKeyboardButton(text="📜 Рецепты", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимия**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients); await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    ings = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for i in ings: builder.add(types.InlineKeyboardButton(text=i, callback_data=f"ing:{i}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Варить!", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 Выбери 2 ингредиента:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ingredient(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing); await state.update_data(mix=mix); await callback.answer(f"+ {ing}")
    await callback.answer()

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data(); mix = data.get('mix', [])
    if len(mix) < 2: await callback.answer("Нужно 2 предмета!", show_alert=True); return
    res = RECIPES.get(tuple(sorted(mix)), "💥 Жижа...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🧪 Результат: {res}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_book")
async def alchemy_book(callback: types.CallbackQuery):
    data = get_data('alchemy').get('sets', {})
    builder = InlineKeyboardBuilder()
    for key, s in data.items(): 
        builder.row(types.InlineKeyboardButton(text=s['name'], callback_data=f"alc_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text("📜 **Книга рецептов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("alc_s:"))
async def alchemy_set_details(callback: types.CallbackQuery):
    set_key = callback.data.split(":")[1]
    alc_set = get_data('alchemy')['sets'][set_key]
    text = f"🧪 **Сет: {alc_set['name']}**\n"
    for p in alc_set['potions']: 
        text += f"🔹 {p['name']}: {p['effect']}\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    ch = [{"title": "🏹 Лучник", "rules": "Только луки", "quest": "Убей Скелетрона"}]
    res = random.choice(ch)
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🎲 {res['title']}\n{res['quest']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 До-ХМ", callback_data="b_l:pre_hm"),
                                          types.InlineKeyboardButton(text="🔴 ХМ", callback_data="b_l:hm"))
    builder.add(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 Боссы:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): 
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("🎯 **Выберите босса:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{st}:{k}"),
                types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    data = get_data('bosses')[st][k]
    txt = data.get(fld, "Нет данных")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К боссу", callback_data=f"b_s:{st}:{k}"))
    if fld == "arena" and "arena_img" in data and data["arena_img"]:
        await callback.message.delete()
        await callback.message.answer_photo(photo=data["arena_img"], caption=f"🏟️ **Арена:**\n\n{txt}", reply_markup=builder.as_markup())
    else: await callback.message.edit_text(f"📝 **Инфо:**\n\n{txt}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for cid, name in {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К боссу", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🛡️ Класс:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items): builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("🎒 Экипировка:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    item = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {item['name']}\n{item['craft']}", show_alert=True)

@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-ХМ", callback_data="ev_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 ХМ", callback_data="ev_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("📅 События:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('events')[st]
    builder = InlineKeyboardBuilder()
    for k, ev in data.items(): builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 Выберите событие:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    ev = get_data('events')[st][k]
    text = f"⚔️ **{ev['name']}**\n🔥 Сложность: {ev.get('difficulty')}\n💰 Профит: {ev.get('profit')}\n\n📢 Триггер: {ev['trigger']}\n🌊 Волны: {ev['waves']}\n🎁 Дроп: {ev['drops']}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{st}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🛡️ Выбери класс:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    sts = {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}
    for k, v in sts.items(): builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes"))
    await callback.message.edit_text("📅 Этап:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_c:"))
async def class_cats(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"),
                types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}"))
    await callback.message.edit_text("Категория:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    data = get_data('classes')[cid]['stages'][sid][cat]
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(data): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    await callback.message.edit_text("🎒 Предмет:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список", callback_data="n_list"),
                types.InlineKeyboardButton(text="🏡 Советы", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 Кто нужен?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = f"👤 **{npc['name']}**\n📥 Приход: {npc.get('arrival')}\n📍 Биом: {npc['biome']}\n🎁 Бонус: {npc.get('bonus')}\n❤️ Любит: {npc['loves']}\n😊 Нравится: {npc['likes']}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 **Советы:**\n1. Не >3 NPC рядом.\n2. Счастье влияет на цены.\n3. Пилоны только у счастливых!"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_fishing")
async def fishing_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🐠 Квесты", callback_data="fish_list"),
                types.InlineKeyboardButton(text="📦 Ящики", callback_data="fish_crates"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🎣 **Рыбалка**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_list")
async def fish_biomes(callback: types.CallbackQuery):
    data = get_data('fishing').get('quests', {})
    builder = InlineKeyboardBuilder()
    for b in data.keys(): builder.add(types.InlineKeyboardButton(text=b, callback_data=f"fish_q:{b}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 Биом:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fish_q:"))
async def fish_biome_info(callback: types.CallbackQuery):
    b = callback.data.split(":")[1]
    data = get_data('fishing').get('quests', {}).get(b, [])
    text = f"📍 **{b}**\n"
    for f in data: text += f"🐟 {f['name']}\n└ 💡 {f['info']}\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_list"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_crates")
async def fish_crates(callback: types.CallbackQuery):
    data = get_data('fishing').get('crates', [])
    text = "📦 **Ящики:**\n"
    for c in data: text += f"{c['name']}\n└ 🎁 {c['drop']}\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы", callback_data="calc_armor"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Слитки", callback_data="calc_ores"))
    builder.row(types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Калькуляторы**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_armor")
async def calc_armor_menu(callback: types.CallbackQuery):
    sets = {"Железо/Свинец": 75, "Золото/Платина": 90, "Святой": 54, "Хлорофит": 54}
    builder = InlineKeyboardBuilder()
    for n, c in sets.items(): builder.row(types.InlineKeyboardButton(text=f"{n} ({c})", callback_data=f"do_arm_c:{n}:{c}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ Сет:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("do_arm_c:"))
async def do_armor_calc(callback: types.CallbackQuery):
    _, n, bars = callback.data.split(":")
    m = 3 if "Железо" in n else 4
    text = f"🛡️ **{n}**\n📦 Слитков: {bars}\n⛏️ Руды: **{int(bars)*m}**"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calc_armor"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    ores = {"Медь (3:1)": 3, "Золото (4:1)": 4, "Адамантит (5:1)": 5}
    builder = InlineKeyboardBuilder()
    for n, r in ores.items(): builder.row(types.InlineKeyboardButton(text=n, callback_data=f"ore_sel:{r}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ Металл:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ore_sel:"))
async def ore_input_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_ratio=callback.data.split(":")[1])
    await state.set_state(CalcState.wait_ore_count)
    await callback.message.answer("🔢 Кол-во слитков:")

@dp.message(CalcState.wait_ore_count)
async def ore_input_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        total = int(message.text) * int(data['current_ratio'])
        await message.answer(f"⛏ Нужно **{total}** руды.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 Цена (в золоте):")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        text = f"💰 **{p} зол.**\n😊 Скидка: {round(p*0.83, 2)}\n❤️ Макс: {round(p*0.67, 2)}"
        await message.answer(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
