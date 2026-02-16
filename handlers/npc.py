from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import json
import os

router = Router()

class NPCCalc(StatesGroup):
    choose_biome = State()
    choose_npc1 = State()
    choose_npc2 = State()
    choose_npc3 = State()

def get_data(filename):
    path = f"data/{filename}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def calculate_happiness(npc_name, partners, biome):
    data = get_data('npcs')
    npc_list = data.get('npcs', [])
    npc = next((n for n in npc_list if n["name"] in npc_name or npc_name in n["name"]), None)
    
    if not npc: return 1.0, []
    
    score = 1.0
    factors = []
    
    # Проверка биома
    if npc.get("biome") == biome:
        score *= 0.9
        factors.append(f"🌳 {biome}")
    
    # Проверка соседей
    for partner in partners:
        if not partner or partner == "None": continue
        # Простая проверка вхождения имени (так как в JSON имена с эмодзи)
        if partner in npc.get("loves", ""):
            score *= 0.88
            factors.append(f"❤️ {partner}")
        elif partner in npc.get("likes", ""):
            score *= 0.94
            factors.append(f"😊 {partner}")
        elif partner in npc.get("dislikes", ""):
            score *= 1.06
            factors.append(f"🤨 {partner}")
        elif partner in npc.get("hates", ""):
            score *= 1.12
            factors.append(f"😡 {partner}")

    return round(score, 2), factors

@router.callback_query(F.data == "m_npcs")
async def npc_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Калькулятор счастья", callback_data="nc_start"))
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("👥 <b>Раздел NPC</b>\n\nИспользуй калькулятор для получения скидок и Пилонов.", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ЛОГИКА КАЛЬКУЛЯТОРА ---

@router.callback_query(F.data == "nc_start")
async def nc_step1(callback: types.CallbackQuery, state: FSMContext):
    biomes = ["Лес", "Снега", "Пустыня", "Джунгли", "Океан", "Освящение", "Пещеры", "Грибной"]
    builder = InlineKeyboardBuilder()
    for b in biomes: builder.add(types.InlineKeyboardButton(text=b, callback_data=f"nc_b:{b}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("🏙 <b>Шаг 1: Выберите биом:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_biome)

@router.callback_query(F.data.startswith("nc_b:"))
async def nc_step2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(biome=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n1:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👤 <b>Шаг 2: Выберите первого NPC:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc1)

@router.callback_query(F.data.startswith("nc_n1:"))
async def nc_step3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc1=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n2:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👥 <b>Шаг 3: Выберите второго NPC:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc2)

@router.callback_query(F.data.startswith("nc_n2:"))
async def nc_step4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc2=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Хватит двоих", callback_data="nc_n3:None"))
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n3:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text("👥 <b>Шаг 4: Добавить третьего NPC?</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc3)

@router.callback_query(F.data.startswith("nc_n3:"))
async def nc_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    npc3 = callback.data.split(":")[1]
    biome, npc1, npc2 = data['biome'], data['npc1'], data['npc2']
    names = [npc1, npc2]
    if npc3 != "None": names.append(npc3)
    
    res_text = f"📊 <b>Результат ({biome}):</b>\n━━━━━━━━━━━━━━"
    for cur in names:
        others = [n for n in names if n != cur]
        mod, facts = calculate_happiness(cur, others, biome)
        status = "✅ <b>ПРОДАСТ ПИЛОН</b>" if mod <= 0.90 else "❌ Нет пилона"
        res_text += f"\n\n👤 <b>{cur}</b>\n└ Цена: <code>{int(mod*100)}%</code> | {status}\n└ <i>{', '.join(facts) if facts else 'Нейтрально'}</i>"

    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Заново", callback_data="nc_start")).row(types.InlineKeyboardButton(text="🏠 К NPC", callback_data="m_npcs"))
    await callback.message.edit_text(res_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "n_list")
async def npc_list(callback: types.CallbackQuery):
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 <b>Выберите жителя для справки:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("n_i:"))
async def npc_info(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next((n for n in get_data('npcs')['npcs'] if n['name'] == name), None)
    txt = (f"👤 <b>{npc['name']}</b>\n━━━━━━━━━━━━━━\n📥 <b>Приход:</b> {npc.get('arrival')}\n"
           f"📍 <b>Биом:</b> {npc['biome']}\n🎁 <b>Бонус:</b> {npc.get('bonus')}\n\n"
           f"❤️ <b>Любит:</b> {npc['loves']}\n😊 <b>Нравится:</b> {npc['likes']}")
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list")).as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 <b>Советы по домам:</b>\n1. Не более 2-3 жителей в одном месте.\n2. Счастье влияет на цены перековки и товаров.\n3. Гоблин и Медсестра — приоритеты для счастья."
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs")).as_markup(), parse_mode="HTML")

