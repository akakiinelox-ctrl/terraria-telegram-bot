import os
import json
import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

# --- ДАННЫЕ ДЛЯ АЛХИМИИ (Интерактив) ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

# --- ЗАГРУЗКА ДАННЫХ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    await message.answer(
        "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я помогу тебе подготовиться к любой угрозе. Выбери раздел:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state)

# ==========================================
# 🧪 РАЗДЕЛ: АЛХИМИЯ (ИНТЕРАКТИВНЫЙ КОТЁЛ)
# ==========================================
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить зелье", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="📜 Книга рецептов", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
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
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    
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
        await callback.answer("Котёл полон! Жми 'Начать варку!'", show_alert=True)

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    
    if len(mix) < 2:
        await callback.answer("Нужно минимум 2 ингредиента!", show_alert=True)
        return

    mix_tuple = tuple(sorted(mix))
    result = RECIPES.get(mix_tuple, "💥 Ба-бах! Получилась бесполезная жижа... Ингредиенты не подошли.")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Сварить еще", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="⬅️ В алхимию", callback_data="m_alchemy"))
    
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
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="alc_book"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 🎲 РАНДОМАЙЗЕР (ОБНОВЛЕНО: ПОДРОБНЫЕ КВЕСТЫ)
# ==========================================
@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    challenges = [
        {
            "title": "🏹 Путь Робин Гуда",
            "desc": "Вы — изгнанный лучник. Ваша связь с технологиями разорвана.",
            "rules": "• Использовать только деревянные или костяные луки.\n• Никакого огнестрела и лазеров.\n• Носить только броню из природных материалов (дерево, тыква, джунгли).",
            "quest": "🎯 **Квест:** Победить Скелетрона, используя только обычные стрелы (без эффектов)."
        },
        {
            "title": "🧨 Безумный Подрывник",
            "desc": "Оружие для слабаков! Настоящие мастера решают проблемы взрывами.",
            "rules": "• Наносить урон боссам только бомбами, динамитом или гранатами.\n• Разрешено использовать ракетницы в Хардмоде.",
            "quest": "🎯 **Квест:** Уничтожить Пожирателя Миров или Мозг Ктулху, не сделав ни одного выстрела из лука или меча."
        },
        {
            "title": "🎣 Дары Океана",
            "desc": "Вы поклялись использовать только то, что дарует вам море.",
            "rules": "• Оружие и броня — только из рыбалки или крафта из океанических ресурсов.\n• Основной источник зелий — только ящики.",
            "quest": "🎯 **Квест:** Добыть 'Акулу-молот' и победить любого босса в океаническом биоме."
        },
        {
            "title": "⚔️ Истинный Рыцарь",
            "desc": "Магия и дальний бой — удел трусов. Только сталь и ближний контакт.",
            "rules": "• Использовать мечи БЕЗ магических снарядов (True Melee).\n• Запрещено использовать йо-йо и копья.",
            "quest": "🎯 **Квест:** Убить Короля Слизней, находясь вплотную к нему 90% времени боя."
        },
        {
            "title": "🍄 Грибной Отшельник",
            "desc": "Вы слишком долго прожили в светящихся грибах и стали их частью.",
            "rules": "• Жить только в грибном биоме (даже в подземелье).\n• Использовать только грибное оружие и экипировку.",
            "quest": "🎯 **Квест:** Построить надземный грибной биом до начала Хардмода и заселить туда Трюфеля сразу после его начала."
        }
    ]
    
    res = random.choice(challenges)
    text = (
        f"🎲 **Челлендж: {res['title']}**\n\n"
        f"📜 *{res['desc']}*\n\n"
        f"⚙️ **Правила:**\n{res['rules']}\n\n"
        f"{res['quest']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎲 Другой челлендж", callback_data="m_random"),
                types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 👾 РАЗДЕЛ: БОССЫ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите категорию боссов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
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
                types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    txt = get_data('bosses')[st][k].get(fld, "Данные обновляются...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text(f"📝 **Информация:**\n\n{txt}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    clss = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for cid, name in clss.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🛡️ **Выберите свой класс:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
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
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("📅 **Выберите этап для просмотра нашествий:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data('events')[stage]
    builder = InlineKeyboardBuilder()
    for key, ev in data.items():
        builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 **Выберите событие для тактического разбора:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data('events')[stage][key]
    text = (f"⚔️ **{ev['name']}**\n━━━━━━━━━━━━━━\n🔥 **Сложность:** {ev.get('difficulty', '???')}\n"
            f"💰 **Профит:** {ev.get('profit', '???')}\n\n📢 **Триггер:** {ev['trigger']}\n"
            f"🌊 **Волны:** {ev['waves']}\n🎁 **Дроп:** {ev['drops']}\n\n🛠 **ТАКТИКА:** \n_{ev.get('arena_tip', 'Стандартная арена.')}_")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 🛡️ РАЗДЕЛ: КЛАССЫ
# ==========================================
@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Выберите класс для изучения билда:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    sts = {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}
    for k, v in sts.items():
        builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
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
    for i, itm in enumerate(data):
        builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    await callback.message.edit_text("🎒 **Выбери предмет для инфо:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

# ==========================================
# 👥 РАЗДЕЛ: NPC (С СТРУКТУРОЙ ИЗ JSON)
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"),
                types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Выберите NPC:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = (f"👤 **{npc['name']}**\n"
           f"━━━━━━━━━━━━━━\n"
           f"📥 **Приход:** {npc.get('arrival', 'Стандарт')}\n"
           f"📍 **Биом:** {npc['biome']}\n"
           f"🎁 **Бонус:** {npc.get('bonus', 'Нет')}\n\n"
           f"❤️ **Любит:** {npc['loves']}\n"
           f"😊 **Нравится:** {npc['likes']}\n"
           f"😐 **Не нравится:** {npc.get('dislikes', 'Нет')}\n"
           f"😡 **Ненавидит:** {npc.get('hates', 'Нет')}")
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
    builder.row(types.InlineKeyboardButton(text="🧪 Советы и Механики", callback_data="fish_gear"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("🎣 **Справочник Рыболова**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_list")
async def fish_biomes(callback: types.CallbackQuery):
    data = get_data('fishing').get('quests', {})
    builder = InlineKeyboardBuilder()
    for biome in data.keys():
        builder.add(types.InlineKeyboardButton(text=biome, callback_data=f"fish_q:{biome}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 **Выбери биом:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("fish_q:"))
async def fish_biome_info(callback: types.CallbackQuery):
    biome = callback.data.split(":")[1]
    data = get_data('fishing').get('quests', {}).get(biome, [])
    text = f"📍 **Биом: {biome}**\n━━━━━━━━━━━━━━\n"
    for fish in data:
        text += f"🐟 **{fish['name']}**\n└ 🌊 Глубина: {fish['height']}\n└ 💡 {fish['info']}\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_list"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_crates")
async def fish_crates(callback: types.CallbackQuery):
    data = get_data('fishing').get('crates', [])
    text = "📦 **Рыболовные ящики:**\n━━━━━━━━━━━━━━\n"
    for crate in data:
        text += f"{crate['name']}\n└ 🎁 Лут: {crate['drop']}\n└ 🍀 Шанс: {crate['chance']}\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "fish_gear")
async def fish_gear(callback: types.CallbackQuery):
    mechanics = get_data('fishing').get('mechanics', {})
    text = "🧪 **Советы и Механики:**\n━━━━━━━━━━━━━━\n"
    for factor in mechanics.get('power_factors', []):
        text += f"• {factor}\n"
    text += "\n🏆 **Награды Энглера:**\n"
    for reward in mechanics.get('rewards', []):
        text += f"• {reward}\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# ==========================================
# 🧮 РАЗДЕЛ: КАЛЬКУЛЯТОР
# ==========================================
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы на Сет Брони", callback_data="calc_armor"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Слитки ➔ Руда", callback_data="calc_ores"))
    builder.row(types.InlineKeyboardButton(text="💰 Скидки Гоблина", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Инженерный отдел**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_armor")
async def calc_armor_menu(callback: types.CallbackQuery):
    sets = {"Железо/Свинец": 75, "Золото/Платина": 90, "Святой сет": 54, "Хлорофит": 54, "Адамантит/Титан": 54}
    builder = InlineKeyboardBuilder()
    for name, count in sets.items():
        builder.row(types.InlineKeyboardButton(text=f"{name} ({count} бар)", callback_data=f"do_arm_c:{name}:{count}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ **Выберите сет:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("do_arm_c:"))
async def do_armor_calc(callback: types.CallbackQuery):
    _, name, bars = callback.data.split(":")
    mult = 3 if "Железо" in name else 4 if "Золото" in name else 5 if "Хлорофит" in name or "Адамантит" in name else 1
    total_ore = int(bars) * mult
    text = f"🛡️ **Комплект: {name}**\n━━━━━━━━━━━━━━\n📦 Слитков: {bars}\n⛏️ Руды: **{total_ore} шт.**"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calc_armor"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    ores = {"Медь/Олово (3:1)": 3, "Железо/Свинец (3:1)": 3, "Серебро/Вольфрам (4:1)": 4, "Золото/Платина (4:1)": 4, "Адамантит/Титан (5:1)": 5, "Хлорофит (5:1)": 5}
    builder = InlineKeyboardBuilder()
    for name, ratio in ores.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"ore_sel:{ratio}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ **Выбери металл для конвертации:**", reply_markup=builder.as_markup())

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