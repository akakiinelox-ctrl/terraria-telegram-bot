import os
import json
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

# Состояния для калькулятора счастья
class NPCCalc(StatesGroup):
    choose_biome = State()
    choose_npc1 = State()
    choose_npc2 = State()
    choose_npc3 = State()

def get_data(filename):
    """Безопасное получение данных из JSON с учетом структуры проекта"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    path = os.path.join(base_dir, "data", f"{filename}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

PYLONS_LIST = [
    ("🌲 Лесной", "Торговец + Гид"),
    ("🌵 Пустынный", "Оружейник + Медсестра"),
    ("❄️ Снежный", "Механик + Гоблин"),
    ("🍄 Грибной", "Трюфель + Гид"),
    ("🌴 Джунгли", "Дриада + Маляр"),
    ("🌊 Океан", "Рыбак + Пират"),
    ("🔮 Святой", "Волшебник + Тусовщица"),
    ("🌋 Пещерный", "Трактирщик + Подрывник")
]

# --- ГЛАВНОЕ МЕНЮ РАЗДЕЛА NPC ---
@router.callback_query(F.data == "m_npcs")
async def npc_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Калькулятор счастья", callback_data="nc_start"))
    builder.row(types.InlineKeyboardButton(text="💎 Гайд по Пилонам", callback_data="n_pylons"))
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    # Кнопка Домой
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "👥 <b>Раздел NPC и Пилонов</b>\n\nРассчитывай счастье для скидок или смотри готовые пары для телепортов.", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- ГАЙД ПО ПИЛОНАМ ---
@router.callback_query(F.data == "n_pylons")
async def pylons_info(callback: types.CallbackQuery):
    text = "💎 <b>Гид по Пилонам</b>\n\nСамые простые пары для каждого биома:\n\n"
    for name, pair in PYLONS_LIST:
        text += f"📍 <b>{name}:</b> {pair}\n"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ЛОГИКА КАЛЬКУЛЯТОРА ---
def calculate_happiness(npc_name, partners, biome):
    data = get_data('npcs')
    npc_list = data.get('npcs', [])
    npc = next((n for n in npc_list if n["name"] in npc_name or npc_name in n["name"]), None)
    if not npc: return 1.0, []
    
    score = 1.0
    factors = []
    if npc.get("biome") == biome:
        score *= 0.9
        factors.append(f"🌳 {biome}")
    
    for partner in partners:
        if not partner or partner == "None": continue
        if partner in npc.get("loves", ""):
            score *= 0.88
            factors.append(f"❤️ {partner}")
        elif partner in npc.get("likes", ""):
            score *= 0.94
            factors.append(f"😊 {partner}")
    return round(score, 2), factors

# --- ШАГИ КАЛЬКУЛЯТОРА ---
@router.callback_query(F.data == "nc_start")
async def nc_step1(callback: types.CallbackQuery, state: FSMContext):
    biomes = ["Лес", "Снега", "Пустыня", "Джунгли", "Океан", "Освящение", "Пещеры", "Грибной"]
    builder = InlineKeyboardBuilder()
    for b in biomes:
        builder.add(types.InlineKeyboardButton(text=b, callback_data=f"nc_b:{b}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🏙 <b>Шаг 1: Выберите биом:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_biome)

@router.callback_query(F.data.startswith("nc_b:"))
async def nc_step2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(biome=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n1:{n['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👤 <b>Шаг 2: Первый житель:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc1)

@router.callback_query(F.data.startswith("nc_n1:"))
async def nc_step3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc1=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n2:{n['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 <b>Шаг 3: Второй сосед:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc2)

@router.callback_query(F.data.startswith("nc_n2:"))
async def nc_step4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(npc2=callback.data.split(":")[1])
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Хватит двоих", callback_data="nc_n3:None"))
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n3:{n['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 <b>Шаг 4: Добавить третьего?</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(NPCCalc.choose_npc3)

@router.callback_query(F.data.startswith("nc_n3:"))
async def nc_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    npc3 = callback.data.split(":")[1]
    biome, npc1, npc2 = data['biome'], data['npc1'], data['npc2']
    names = [npc1, npc2]
    if npc3 != "None": names.append(npc3)
    
    res_text = f"📊 <b>Результат ({biome}):</b>"
    for cur in names:
        others = [n for n in names if n != cur]
        mod, facts = calculate_happiness(cur, others, biome)
        status = "✅ <b>Пилон</b>" if mod <= 0.90 else "❌"
        res_text += f"\n\n👤 <b>{cur}</b>: {int(mod*100)}% | {status}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Заново", callback_data="nc_start"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К разделу NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(res_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

# --- СПИСОК ЖИТЕЛЕЙ ---
@router.callback_query(F.data == "n_list")
async def npc_list(callback: types.CallbackQuery):
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👤 <b>Выберите жителя:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("n_i:"))
async def npc_info(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc_list_data = get_data('npcs').get('npcs', [])
    npc = next((n for n in npc_list_data if n['name'] == name), None)
    
    if not npc:
        await callback.answer("Ошибка: Житель не найден", show_alert=True)
        return

    txt = (f"👤 <b>{npc['name']}</b>\n\n📥 Приход: {npc.get('arrival', 'Неизвестно')}\n"
           f"📍 Биом: {npc['biome']}\n❤️ Любит: {npc['loves']}\n😊 Нравится: {npc['likes']}")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- СОВЕТЫ ---
@router.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 <b>Советы по счастью:</b>\n1. Не селите больше 3 NPC в одном месте.\n2. Счастье снижает цены на 25%.\n3. Пилон продается при счастье < 90%."
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
