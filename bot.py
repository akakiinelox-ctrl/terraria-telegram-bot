import os
import json
import logging
import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") 
ADMIN_ID = 599835907  # Твой ID для админ-доступа

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ (FSM) ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

class NPCCalc(StatesGroup):
    choose_biome = State()
    choose_npc1 = State()
    choose_npc2 = State()
    choose_npc3 = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
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

def calculate_happiness(npc_name, partners, biome):
    npc_list = get_data('npcs').get('npcs', [])
    npc = next((n for n in npc_list if n["name"] == npc_name), None)
    if not npc: return 1.0, []
    
    score = 1.0
    factors = []
    
    # Проверка биома
    if npc.get("biome") == biome:
        score *= 0.9
        factors.append(f"🌳 Любимый биом ({biome})")
    
    # Проверка соседей
    for partner in partners:
        if not partner or partner == "None": continue
        if partner in npc.get("loves", ""):
            score *= 0.88
            factors.append(f"❤️ Обожает {partner}")
        elif partner in npc.get("likes", ""):
            score *= 0.94
            factors.append(f"😊 Нравится {partner}")
        elif partner in npc.get("dislikes", ""):
            score *= 1.06
            factors.append(f"🤨 Не любит {partner}")
        elif partner in npc.get("hates", ""):
            score *= 1.12
            factors.append(f"😡 Ненавидит {partner}")

    return round(score, 2), factors

# --- ДАННЫЕ (РЕЦЕПТЫ И ЧЕК-ЛИСТЫ) ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации (восст. HP)",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника (+урон стрел)",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

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

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 
    users = get_data('users')
    total = len(users)
    active_today = 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    for u in users.values():
        if u.get("last_active") == today_str: active_today += 1
    await message.answer(f"📊 **Статистика:**\n👤 Всего: {total}\n🔥 Сегодня: {active_today}", parse_mode="Markdown")

@dp.message(Command("link"))
async def generate_ref_link(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID or not command.args: return
    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start={command.args.strip()}"
    await message.answer(f"✅ Ссылка: `{link}`", parse_mode="Markdown")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref_source = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Выбери раздел для изучения:"
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, None, state)

# ==========================================
# 👥 РАЗДЕЛ NPC И СУПЕР-КАЛЬКУЛЯТОР
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Калькулятор счастья", callback_data="nc_start"))
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **Раздел NPC**\n\nРассчитай счастье для скидок или изучи жителей.", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "nc_start")
async def nc_step1(callback: types.CallbackQuery, state: FSMContext):
    biomes = ["Лес", "Снега", "Пустыня", "Джунгли", "Океан", "Освящение", "Пещеры", "Грибной"]
    builder = InlineKeyboardBuilder()
    for b in biomes: builder.add(types.InlineKeyboardButton(text=b, callback_data=f"nc_b:{b}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("🏙 **Шаг 1: Выберите биом:**", reply_markup=builder.as_markup())
    await state.set_state(NPCCalc.choose_biome)

@dp.callback_query(F.data.startswith("nc_b:"))
async def nc_step2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(biome=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n1:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👤 **Шаг 2: Выберите 1-го NPC:**", reply_markup=builder.as_markup())
    await state.set_state(NPCCalc.choose_npc1)

@dp.callback_query(F.data.startswith("nc_n1:"))
async def nc_step3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc1=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n2:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👥 **Шаг 3: Выберите 2-го NPC:**", reply_markup=builder.as_markup())
    await state.set_state(NPCCalc.choose_npc2)

@dp.callback_query(F.data.startswith("nc_n2:"))
async def nc_step4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc2=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Расчёт (только двое)", callback_data="nc_n3:None"))
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n3:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👥 **Шаг 4: Добавить 3-го соседа?**", reply_markup=builder.as_markup())
    await state.set_state(NPCCalc.choose_npc3)

@dp.callback_query(F.data.startswith("nc_n3:"))
async def nc_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    npc3 = callback.data.split(":")[1]
    biome, npc1, npc2 = data['biome'], data['npc1'], data['npc2']
    names = [npc1, npc2]
    if npc3 != "None": names.append(npc3)
    
    res_text = f"📊 **Итоги расселения: {biome}**\n━━━━━━━━━━━━━━"
    for cur in names:
        others = [n for n in names if n != cur]
        mod, facts = calculate_happiness(cur, others, biome)
        status = "✅ <b>ПРОДАСТ ПИЛОН</b>" if mod <= 0.90 else "❌ Нет"
        res_text += f"\n\n👤 <b>{cur}</b>\n└ Цена: <code>{int(mod*100)}%</code> | {status}\n└ <i>{', '.join(facts) if facts else 'Нейтрально'}</i>"

    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Заново", callback_data="nc_start")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(res_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Список всех жителей:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = (f"👤 **{npc['name']}**\n━━━━━━━━━━━━━━\n📥 **Приход:** {npc.get('arrival', 'Стандарт')}\n"
           f"📍 **Биом:** {npc['biome']}\n🎁 **Бонус:** {npc.get('bonus', 'Нет')}\n\n"
           f"❤️ **Любит:** {npc['loves']}\n😊 **Нравится:** {npc['likes']}")
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list")).as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 **Советы по расселению:**\n1. Не более 3 NPC рядом.\n2. Счастье влияет на цены.\n3. Пилоны продаются только у счастливых NPC!"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs")).as_markup())

# ==========================================
# 👾 БОССЫ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="b_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="b_l:hm")).row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите категорию:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("🎯 **Выберите босса:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Снаряжение", callback_data=f"b_g:{st}:{k}"), types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"), types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_detail(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    txt = get_data('bosses')[st][k].get(fld, "Нет данных.")
    await callback.message.edit_text(f"📝 **Инфо:**\n\n{txt}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}")).as_markup(), parse_mode="Markdown")

# ==========================================
# ⚔️ СОБЫТИЯ
# ==========================================
@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 Pre-HM", callback_data="ev_l:pre_hm"), types.InlineKeyboardButton(text="🔴 HM", callback_data="ev_l:hm")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("📅 **Выберите этап событий:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('events')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"ev_i:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 **Нашествия:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    ev = get_data('events')[st][k]
    text = (f"⚔️ **{ev['name']}**\n━━━━━━━━━━━━━━\n🔥 **Сложность:** {ev.get('difficulty', '???')}\n"
            f"💰 **Профит:** {ev.get('profit', '???')}\n\n📢 **Триггер:** {ev['trigger']}\n"
            f"🌊 **Волны:** {ev['waves']}\n🎁 **Дроп:** {ev['drops']}\n\n🛠 **ТАКТИКА:** \n_{ev.get('arena_tip', 'Стандартная арена.')}_")
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{st}")).as_markup(), parse_mode="Markdown")

# ==========================================
# 📋 ЧЕК-ЛИСТЫ
# ==========================================
@dp.callback_query(F.data == "m_checklist")
async def checklist_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for k, v in CHECKLIST_DATA.items(): builder.row(types.InlineKeyboardButton(text=f"📍 {v['name']}", callback_data=f"chk_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("📋 **Чек-листы готовности:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("chk_s:"))
async def checklist_show(callback: types.CallbackQuery):
    cat = callback.data.split(":")[1]
    items = CHECKLIST_DATA[cat]['items']
    text = f"📋 **{CHECKLIST_DATA[cat]['name']}**\n━━━━━━━━━━━━━━\n\n"
    for icon, desc in items: text += f"{icon} — {desc}\n"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist")).as_markup())

# ==========================================
# 🎣 РЫБАЛКА
# ==========================================
@dp.callback_query(F.data == "m_fishing")
async def fishing_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🐠 Квесты", callback_data="fish_q"), types.InlineKeyboardButton(text="📦 Ящики", callback_data="fish_c")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🎣 **Рыбалка:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_q")
async def fish_quests_biomes(callback: types.CallbackQuery):
    data = get_data('fishing').get('quests', {})
    builder = InlineKeyboardBuilder()
    for b in data.keys(): builder.add(types.InlineKeyboardButton(text=b, callback_data=f"fq_b:{b}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 **Биом квеста:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fq_b:"))
async def fish_quest_list(callback: types.CallbackQuery):
    b = callback.data.split(":")[1]
    data = get_data('fishing').get('quests', {}).get(b, [])
    txt = f"📍 **Биом: {b}**\n\n"
    for f in data: txt += f"🐟 **{f['name']}**\n└ 💡 {f['info']}\n\n"
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_q")).as_markup())

@dp.callback_query(F.data == "fish_c")
async def fish_crates_list(callback: types.CallbackQuery):
    data = get_data('fishing').get('crates', [])
    txt = "📦 **Ящики:**\n\n"
    for c in data: txt += f"🔹 {c['name']}\n└ 🎁 Лут: {c['drop']}\n\n"
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing")).as_markup())

# ==========================================
# 🧪 АЛХИМИЯ
# ==========================================
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"), types.InlineKeyboardButton(text="📜 Книга", callback_data="alc_book")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🧪 **Алхимия:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def alc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    ings = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for i in ings: builder.add(types.InlineKeyboardButton(text=i, callback_data=f"ing:{i}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Сварить!", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 **Выбери 2 ингредиента:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def alc_add(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing)
        await state.update_data(mix=mix)
        await callback.answer(f"Добавлено: {ing}")
    else: await callback.answer("Максимум 2!")

@dp.callback_query(F.data == "alc_mix")
async def alc_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2: return await callback.answer("Нужно 2 ингредиента!")
    res = RECIPES.get(tuple(sorted(mix)), "💥 Ошибка в варке...")
    await callback.message.edit_text(f"🧪 **Результат:**\n\n{res}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Сварить еще", callback_data="alc_craft")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup())
    await state.clear()

# ==========================================
# 🎲 РАНДОМ
# ==========================================
@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    challenges = ["🏹 Путь Робин Гуда: Луки, без брони.", "🧨 Подрывник: Только взрывчатка.", "⚔️ Истинный Воин: Мечи без снарядов."]
    await callback.message.edit_text(f"🎲 **Челлендж:**\n\n{random.choice(challenges)}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Другой", callback_data="m_random")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main")).as_markup(), parse_mode="Markdown")

# --- ОСТАЛЬНОЕ ---
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"), types.InlineKeyboardButton(text="⛏️ Руда", callback_data="calc_ores")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Расчеты:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_goblin")
async def goblin_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 **Введите цену перековки (золото):**")

@dp.message(CalcState.wait_goblin_price)
async def goblin_finish(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        txt = (f"💰 **Для {p} золота:**\n\n😐 База: {p}\n😊 Скидка 17%: {round(p*0.83, 2)}\n❤️ Макс 33%: {round(p*0.67, 2)}")
        await message.answer(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("Число!")

@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Классы:**", reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

