import os
import json
import logging
import asyncio
import random
import aiohttp
import html  # Для безопасной отправки текста ИИ
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

class AIState(StatesGroup): 
    waiting_for_question = State()

# --- ДАННЫЕ (Гайды и рецепты сохранены) ---
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

# --- ИИ ГИД (БЕЗОПАСНЫЙ ЗАПРОС) ---
async def get_ai_guide_answer(user_text):
    url = "https://text.pollinations.ai/" 
    system_prompt = (
        "Ты — Гид из игры Terraria. Твоя задача — давать максимально точные советы игрокам на основе официальной вики Terraria. "
        "Говори на русском языке. Будь полезным, мудрым и дружелюбным. "
        "Если вопрос не про Террарию, вежливо переведи разговор на игру и выживание в ней."
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
                return "Мои мысли сейчас затуманены... Спроси позже, путешественник."
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Здесь слишком опасно сейчас, я не могу сосредоточиться. Приходи позже!"

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ ВАС)
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    users = get_data('users')
    sources = {}
    for u in users.values():
        src = u.get("source", "organic")
        sources[src] = sources.get(src, 0) + 1
    text = f"📊 Всего юзеров: {len(users)}\n\n📢 Источники:\n"
    for s, c in sources.items(): text += f"• {s}: {c}\n"
    await message.answer(text)

@dp.message(Command("link"))
async def generate_ref_link(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    if not command.args: return await message.answer("❌ Используй: `/link tiktok`")
    bot_info = await bot.get_me()
    await message.answer(f"✅ https://t.me/{bot_info.username}?start={command.args.strip()}")

@dp.message(F.photo)
async def get_photo_id(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🖼 ID фото: `{message.photo[-1].file_id}`")

@dp.message(F.video)
async def get_video_id(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"📹 ID видео: `{message.video.file_id}`")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref = command.args if command and hasattr(command, 'args') and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref)
    
    builder = InlineKeyboardBuilder()
    # Кнопка ИИ Гида вместо поиска
    builder.row(types.InlineKeyboardButton(text="🧔 Спросить Гида (AI Поиск)", callback_data="m_ai"))
    
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"), types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"), types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"), types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"), types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    await message.answer("🛠 <b>Terraria Tactical Assistant</b>\n\nПривет, путешественник! Я помогу тебе выжить. Что тебя интересует?", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    save_user(callback.from_user.id, callback.from_user.username)
    await cmd_start(callback.message, None, state)

# ==========================================
# 🗣 ДИАЛОГ С ГИДОМ (ИИ)
# ==========================================
@dp.callback_query(F.data == "m_ai")
async def ai_entry(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AIState.waiting_for_question)
    await callback.message.edit_text(
        "🧔 <b>Гид готов дать совет.</b>\n\nЗадай мне любой вопрос о предметах, боссах или крафте в Terraria.\n\n"
        "✍️ <i>Напиши свой вопрос ниже:</i>",
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
    
    # Экранируем HTML спецсимволы, чтобы сообщение не ломалось
    safe_answer = html.escape(answer)
    await message.answer(f"🧔 <b>Гид:</b>\n\n{safe_answer}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

# --- (ОСТАЛЬНЫЕ ФУНКЦИИ КНОПОК И ГАЙДОВ ОСТАЛИСЬ БЕЗ ИЗМЕНЕНИЙ) ---

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
    for k, s in data.items(): builder.row(types.InlineKeyboardButton(text=s['name'], callback_data=f"alc_s:{k}"))
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

@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    await callback.message.edit_text("📅 <b>События:</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="ev_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="ev_l:hm")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    for key, ev in get_data('events')[stage].items(): builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{stage}:{key}"))
    await callback.message.edit_text("🌊 <b>Выбери:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data('events')[stage][key]
    await callback.message.edit_text(f"⚔️ <b>{ev['name']}</b>\n\n📢 {ev['trigger']}\n🎁 {ev['drops']}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for k, v in get_data('classes').items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    await callback.message.edit_text("🛡️ <b>Классы:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    for k, v in {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}.items(): builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    await callback.message.edit_text("📅 <b>Этап:</b>", reply_markup=builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("cl_c:"))
async def class_cats(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    await callback.message.edit_text("Что смотрим?", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"), types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons")).row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"), types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(get_data('classes')[cid]['stages'][sid][cat]): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    await callback.message.edit_text("🎒 <b>Выбери предмет:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    await callback.message.edit_text("👥 <b>NPC</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="📜 Список", callback_data="n_list"), types.InlineKeyboardButton(text="🏡 Советы", callback_data="n_tips")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for n in get_data('npcs')['npcs']: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    await callback.message.edit_text("👤 <b>NPC:</b>", reply_markup=builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == callback.data.split(":")[1])
    await callback.message.edit_text(f"👤 <b>{npc['name']}</b>\n📍 {npc['biome']}\n❤️ {npc['loves']}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    await callback.message.edit_text("🏡 Счастье влияет на цены!", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_fishing")
async def fishing_main(callback: types.CallbackQuery):
    await callback.message.edit_text("🎣 <b>Рыбалка</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🐠 Квесты", callback_data="fish_list"), types.InlineKeyboardButton(text="📦 Ящики", callback_data="fish_crates")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "fish_list")
async def fish_biomes(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for biome in get_data('fishing').get('quests', {}).keys(): builder.add(types.InlineKeyboardButton(text=biome, callback_data=f"fish_q:{biome}"))
    await callback.message.edit_text("📍 <b>Биом:</b>", reply_markup=builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("fish_q:"))
async def fish_biome_info(callback: types.CallbackQuery):
    biome = callback.data.split(":")[1]
    text = f"📍 <b>{biome}</b>\n"
    for f in get_data('fishing').get('quests', {}).get(biome, []): text += f"🐟 {f['name']}\n"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_list")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "fish_crates")
async def fish_crates(callback: types.CallbackQuery):
    await callback.message.edit_text("📦 Ящики содержат руду!", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    await callback.message.edit_text("🧮 <b>Калькулятор</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🛡️ Сеты", callback_data="calc_armor"), types.InlineKeyboardButton(text="⛏️ Руда", callback_data="calc_ores")).row(types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"), types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "calc_armor")
async def calc_armor_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for n, c in {"Железо": 75, "Золото": 90, "Святой": 54}.items(): builder.row(types.InlineKeyboardButton(text=f"{n} ({c})", callback_data=f"do_arm_c:{n}:{c}"))
    await callback.message.edit_text("🛡️ <b>Выбери сет:</b>", reply_markup=builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("do_arm_c:"))
async def do_armor_calc(callback: types.CallbackQuery):
    _, name, bars = callback.data.split(":")
    await callback.message.edit_text(f"🛡️ <b>{name}</b>: Нужно {int(bars) * (3 if 'Железо' in name else 4)} руды.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calc_armor")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    await callback.message.edit_text("⛏ <b>Металл:</b>", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Медь (3:1)", callback_data="ore_sel:3"), types.InlineKeyboardButton(text="Золото (4:1)", callback_data="ore_sel:4")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ore_sel:"))
async def ore_input_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_ratio=callback.data.split(":")[1]); await state.set_state(CalcState.wait_ore_count); await callback.message.answer("🔢 Слитков:")

@dp.message(CalcState.wait_ore_count)
async def ore_input_finish(message: types.Message, state: FSMContext):
    data = await state.get_data(); await state.clear()
    try: await message.answer(f"⛏ Нужно {int(message.text) * int(data['current_ratio'])} руды.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
    except: await message.answer("❌ Число!")

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price); await callback.message.answer("💰 Цена:")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    await state.clear()
    try: p = float(message.text.replace(",", ".")); await message.answer(f"💰 Скидка: {round(p*0.83, 2)}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
    except: await message.answer("❌ Число!")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
