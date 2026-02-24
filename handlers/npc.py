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
    builder.row(types.InlineKeyboardButton(text="📋 Список NPC", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🛖 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "👥 <b>Раздел NPC и Пилонов</b>\n\nРассчитывай счастье для скидок или смотри готовые пары для телепортов.", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

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
    await callback.answer()

# --- ИНФОРМАЦИЯ О ЖИТЕЛЕ ---
@router.callback_query(F.data.startswith("n_i:"))
async def npc_info(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc_list_data = get_data('npcs').get('npcs', [])
    npc = next((n for n in npc_list_data if n['name'] == name), None)
    
    if not npc:
        await callback.answer("Ошибка: Житель не найден", show_alert=True)
        return

    txt = (
        f"📜 <b>Информация о {name}</b>\n\n"
        f"🏠 <b>Приход:</b> {npc.get('arrival', 'Неизвестно')}\n"
        f"🌍 <b>Биом:</b> {npc['biome']}\n\n"
        f"❤️ <b>Любит:</b> {npc.get('loves', 'Никого')}\n"
        f"😊 <b>Нравится:</b> {npc.get('likes', 'Никого')}\n"
        f"❌ <b>Не любит:</b> {npc.get('dislikes', 'Никого')}\n"
        f"😡 <b>Ненавидит:</b> {npc.get('hates', 'Никого')}\n\n"
        f"🎁 <b>Бонус:</b> {npc.get('bonus', '—')}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))

    await callback.message.edit_text(txt, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

# --- СОВЕТЫ ПО СТРОИТЕЛЬСТВУ ДОМОВ (полностью на русском) ---
@router.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Гайд по строительству домов для NPC (1.4.4+)</b>\n\n"
        "Сейчас покажу всё с примерами и фото. Листай вниз 👇",
        parse_mode="HTML"
    )
    await callback.answer()

    # Фото-примеры
    await callback.message.answer_photo(
        photo="https://static.wikia.nocookie.net/terraria_gamepedia/images/3/31/Valid_House_Door.png/revision/latest",
        caption="✅ Пример правильного дома с дверью (9×7 блоков)"
    )

    await callback.message.answer_photo(
        photo="https://static.wikia.nocookie.net/terraria_gamepedia/images/e/e5/Npccell.png/revision/latest",
        caption="🟩 Самый маленький возможный дом (3×10 блоков)"
    )

    await callback.message.answer_photo(
        photo="https://static.wikia.nocookie.net/terraria_gamepedia/images/8/86/Simpliest_Housing.png/revision/latest",
        caption="🏡 Классический простой дом с мебелью"
    )

    tips_text = (
        "📋 <b>12 главных правил для правильного дома:</b>\n\n"
        "1. Общая площадь — от 60 до 749 блоков.\n"
        "2. Обязательно должна быть дверь, люк или высокие ворота.\n"
        "3. Фоновая стена (стены фона — не пустота!).\n"
        "4. Мебель: 1 предмет комфорта (стул, трон, кровать) + 1 плоская поверхность (стол, верстак).\n"
        "5. Минимум 1 источник света (факел, свеча, люстра).\n"
        "6. Минимум 4 свободных блока пола для NPC.\n"
        "7. Ничего лишнего внутри комнаты (кроме мебели).\n"
        "8. Не больше 3 NPC в радиусе 120 блоков (для счастья).\n"
        "9. Дом должен быть в правильном биоме для пилона.\n"
        "10. Проверяй в игре кнопкой «Жильё» — должен быть зелёным.\n"
        "11. Пол и потолок можно делать из платформ.\n"
        "12. Идеально: любимый биом + любимый сосед = скидки до 33% \n\n"
        "💡 Для расчёта счастья используй калькулятор выше."
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад в NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))

    await callback.message.answer(
        tips_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
