import os
import json
import logging
import asyncio
import random
import aiohttp
import html
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

# --- СТАНЫ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

class AIState(StatesGroup): 
    waiting_for_question = State()

# --- ДАННЫЕ ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

CHECKLIST_DATA = {
    "start": { "name": "🌱 Начало (Pre-Boss)", "items": [("🏠 Деревня", "Построено 5+ домов."), ("❤️ Жизнь", "Минимум 200 HP."), ("💎 Броня", "Золото/Платина."), ("🔗 Мобильность", "Крюк и сапоги."), ("⛏️ Кирка", "Золотая кирка.")] },
    "pre_hm": { "name": "🌋 Финал Pre-HM", "items": [("⚔️ Грань Ночи", "Топовый меч."), ("❤️ 400 HP", "Максимум сердец."), ("🌋 Арена", "Дорожка в аду."), ("🌳 Карантин", "Туннели от порчи."), ("🎒 Аксессуары", "Перекованы на защиту.")] },
    "hardmode_start": { "name": "⚙️ Ранний Хардмод", "items": [("⚒️ Кузня", "Сломаны алтари."), ("🧚 Крылья", "Найдены крылья."), ("🍏 500 HP", "Фрукты жизни."), ("🛡️ Броня", "Титан/Адамантит."), ("🔑 Ферма", "Ключи биомов.")] },
    "endgame": { "name": "🌙 Финал (Мунлорд)", "items": [("🛸 НЛО", "Маунт с тарелки."), ("🔫 Оружие", "Пушки башен."), ("🩺 Арена", "Медсестра и мед."), ("🏆 Броня", "Люминит.")] }
}

# --- ФУНКЦИИ ДАННЫХ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception:
        return {}

def save_user(user_id, username, source="organic"):
    users = get_data('users')
    user_id_str = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_id_str not in users:
        users[user_id_str] = {"username": username, "join_date": today, "source": source, "last_active": today, "activity_count": 1}
    else:
        users[user_id_str].update({"last_active": today, "activity_count": users[user_id_str].get("activity_count", 0) + 1, "username": username})

    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# --- ИИ ГИД (БЕСПЛАТНЫЙ API) ---
async def get_ai_guide_answer(user_text):
    # Используем Pollinations.ai (бесплатный доступ к GPT-моделям)
    url = "https://text.pollinations.ai/" 
    system_prompt = (
        "Ты — Гид из игры Terraria. Твоя задача — помогать игрокам советами на русском языке. "
        "Говори дружелюбно, используй термины игры (крафт, биомы, боссы). "
        "Если вопрос не про Террарию, вежливо переведи тему на игру."
    )
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "model": "openai"
            }
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return await resp.text()
                return "Хм... Что-то мешает мне сосредоточиться. Спроси позже."
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Звёзды сейчас не благосклонны. Я не могу ответить."

# --- ПОИСК WIKI ---
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
# 🛡️ АДМИН-ПАНЕЛЬ
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    users = get_data('users')
    sources = {}
    for u in users.values():
        src = u.get("source", "organic")
        sources[src] = sources.get(src, 0) + 1
    text = f"📊 <b>Всего юзеров: {len(users)}</b>\n\n📢 <b>Источники:</b>\n"
    for s, c in sources.items(): text += f"• {s}: {c}\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("link"))
async def generate_ref_link(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    if not command.args: return await message.answer("❌ Пиши: <code>/link tiktok</code>", parse_mode="HTML")
    bot_info = await bot.get_me()
    await message.answer(f"✅ Ссылка:\n<code>https://t.me/{bot_info.username}?start={command.args.strip()}</code>", parse_mode="HTML")

@dp.message(F.photo)
async def get_photo_id(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🖼 ID фото: <code>{message.photo[-1].file_id}</code>", parse_mode="HTML")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref = command.args if command and hasattr(command, 'args') and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧔 Спросить Гида (AI)", callback_data="m_ai"))
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск предмета / Гайд", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"), types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"), types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"), types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"), types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    await message.answer("🛠 <b>Terraria Tactical Assistant</b>\n\nПривет, Террариец! Я помогу тебе подготовиться к любой угрозе.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    save_user(callback.from_user.id, callback.from_user.username)
    await cmd_start(callback.message, None, state)

# ==========================================
# 🗣 ДИАЛОГ С ГИДОМ (AI)
# ==========================================
@dp.callback_query(F.data == "m_ai")
async def ai_entry(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AIState.waiting_for_question)
    await callback.message.edit_text(
        "🧔 <b>Я слушаю тебя.</b>\n\nСпроси меня о крафте, боссах или как выжить в этом мире.\n\n"
        "✍️ <i>Напиши свой вопрос:</i>",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")).as_markup(),
        parse_mode="HTML"
    )

@dp.message(AIState.waiting_for_question)
async def ai_response(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, "typing")
    answer = await get_ai_guide_answer(message.text)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❓ Еще вопрос", callback_data="m_ai"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    
    await message.answer(f"🧔 <b>Гид:</b>\n\n{html.escape(answer)}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

# ==========================================
# 🔍 ПОИСК (Wiki)
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

# --- (ФУНКЦИИ КНОПОК И КАТЕГОРИЙ - БЕЗ ИЗМЕНЕНИЙ) ---

@dp.callback_query(F.data == "m_checklist")
async def checklist_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items(): builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_cat:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🗺 <b>Карта прогресса Terraria</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("chk_cat:"))
async def checklist_start(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    await state.update_data(current_cat=cat, completed=[])
    await show_checklist(callback.message, cat, [])

async def show_checklist(message: types.Message, cat, completed_indices):
    builder = InlineKeyboardBuilder()
    items = CHECKLIST_DATA[cat]['items']
    total, done = len(items), len(completed_indices)
    perc, bar = int((done / total) * 100), "🟩" * done + "⬜" * (total - done)
    for i, (name, _) in enumerate(items):
        status = "✅" if i in completed_indices else "⭕"
        builder.row(types.InlineKeyboardButton(text=f"{status} {name}", callback_data=f"chk_tog:{i}"))
    builder.row(types.InlineKeyboardButton(text="📊 Анализ", callback_data="chk_res"), types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    await message.edit_text(f"📋 <b>Этап: {CHECKLIST_DATA[cat]['name']}</b>\n┃ {bar} {perc}%\n┗━━━━━━━━━━━━━━", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("chk_tog:"))
async def toggle_item(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])
    data = await state.get_data()
    cat, completed = data.get('current_cat'), data.get('completed', [])
    if index in completed: completed.remove(index)
    else: 
        completed.append(index)
        await callback.answer(f"💡 {CHECKLIST_DATA[cat]['items'][index][1]}", show_alert=True)
    await state.update_data(completed=completed)
    await show_checklist(callback.message, cat, completed)

@dp.callback_query(F.data == "chk_res")
async def checklist_result(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat, count = data.get('current_cat'), len(data.get('completed', []))
    total = len(CHECKLIST_DATA[cat]['items'])
    res = "👑 <b>МАСТЕР ЭТАПА</b>" if count == total else "⚔️ <b>ОПЫТНЫЙ ВОИН</b>" if count >= total // 2 else "💀 <b>СМЕРТНИК</b>"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"chk_cat:{cat}"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"), types.InlineKeyboardButton(text="📜 Книга", callback_data="alc_book")).row(types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("✨ <b>Алхимия</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    for ing in ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]: builder.add(types.InlineKeyboardButton(text=ing, callback_data=f"ing:{ing}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Варить!", callback_data="alc_mix"), types.InlineKeyboardButton(text="🏠 Главный экран", callback_data="to_main"))
    await callback.message.edit_text("🌿 <b>Выбери 2 ингредиента:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ing:"))
async def add_ingredient(callback: types.CallbackQuery, state: FSMContext):
    ing, data = callback.data.split(":")[1], await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2:
        if ing not in mix: mix.append(ing); await state.update_data(mix=mix); await callback.answer(f"Добавлено: {ing}")
        else: await callback.answer("Уже в котле!")
    else: await callback.answer("Котёл полон!")

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if len(data.get('mix', [])) < 2: return await callback.answer("Нужно 2 ингредиента!")
    result = RECIPES.get(tuple(sorted(data['mix'])), "💥 Ошибка...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Еще", callback_data="alc_craft"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🧪 <b>Результат:</b>\n\n{result}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "alc_book")
async def alchemy_book(callback: types.CallbackQuery):
    data = get_data('alchemy').get('sets', {})
    builder = InlineKeyboardBuilder()
    for k, s in data.items(): builder.row(types.InlineKeyboardButton(text=s['name'], callback_data=f"alc_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text("📜 <b>Рецепты:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("alc_s:"))
async def alchemy_set_details(callback: types.CallbackQuery):
    alc_set = get_data('alchemy')['sets'][callback.data.split(":")[1]]
    text = f"🧪 <b>Сет: {alc_set['name']}</b>\n\n"
    for p in alc_set['potions']: text += f"🔹 {p['name']}\n└ {p['effect']}\n\n"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="alc_book")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    ch = random.choice([{"t": "🏹 Робин Гуд", "q": "Луки только!"}, {"t": "🧨 Подрывник", "q": "Взрывчатка!"}])
    await callback.message.edit_text(f"🎲 <b>{ch['t']}</b>\n\n{ch['q']}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎲 Еще", callback_data="m_random"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    await callback.message.edit_text("👹 <b>Категория:</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="b_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="b_l:hm")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    for k, v in get_data('bosses')[st].items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🎯 <b>Цель:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🛡️ Эквип", callback_data=f"b_g:{st}:{k}"), types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops")).row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"), types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    try: await callback.message.edit_text(f"📖 <b>{boss['name']}</b>\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="HTML")
    except: await callback.message.delete(); await callback.message.answer(f"📖 <b>{boss['name']}</b>\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    data = get_data('bosses')[st][k]
    txt = data.get(fld, "...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    if fld == "arena" and "arena_img" in data and data["arena_img"]:
        await callback.message.delete()
        await callback.message.answer_photo(photo=data["arena_img"], caption=f"🏟️ <b>Арена:</b>\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="HTML")
    else: await callback.message.edit_text(f"📝 {txt}", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for cid, name in {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}.items(): builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    await callback.message.edit_text("🛡️ <b>Класс:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(get_data('bosses')[st][k]['classes'][cid]): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    await callback.message.edit_text("🎒 <b>Предметы:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    itm = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['craft']}", show_alert=True)

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())