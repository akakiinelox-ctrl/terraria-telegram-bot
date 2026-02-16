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
TOKEN = os.getenv("BOT_TOKEN")  # Токен берется из переменных среды
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
        users[user_id].update({"username": username})

    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Ошибка сохранения юзера: {e}")

def calculate_happiness(npc_name, partner_name, biome):
    npc_list = get_data('npcs').get('npcs', [])
    npc = next((n for n in npc_list if n["name"] == npc_name), None)
    if not npc: return 1.0, []
    
    score = 1.0
    factors = []
    
    # Проверка биома
    if npc.get("biome") == biome:
        score *= 0.9
        factors.append(f"✅ Любимый биом ({biome})")
    
    # Проверка соседа (упрощенный поиск по строке)
    if partner_name:
        if partner_name in npc.get("loves", ""):
            score *= 0.88
            factors.append(f"❤️ Обожает {partner_name}")
        elif partner_name in npc.get("likes", ""):
            score *= 0.94
            factors.append(f"😊 Нравится {partner_name}")
        elif partner_name in npc.get("dislikes", ""):
            score *= 1.06
            factors.append(f"🤨 Не любит {partner_name}")
        elif partner_name in npc.get("hates", ""):
            score *= 1.12
            factors.append(f"😡 Ненавидит {partner_name}")

    return round(score, 2), factors

# --- ДАННЫЕ (РЕЦЕПТЫ И ЧЕК-ЛИСТЫ) ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

CHECKLIST_DATA = {
    "start": {"name": "🌱 Начало (Pre-Boss)", "items": [("🏠 Деревня", "Построено 5+ домов."), ("❤️ Жизнь", "5+ Кристаллов жизни."), ("💎 Броня", "Золото/Платина."), ("🔗 Кошка", "Есть крюк."), ("⛏️ Инструменты", "Кирка для Метеорита.")]},
    "pre_hm": {"name": "🌋 Финал Pre-HM", "items": [("⚔️ Оружие", "Грань Ночи или аналог."), ("❤️ 400 HP", "Максимум здоровья."), ("🌋 Дорога", "Трасса в аду 1500+ блоков."), ("🌳 Карантин", "Туннели вокруг порчи.")]},
    "hardmode_start": {"name": "⚙️ Ранний Хардмод", "items": [("⚒️ Кузня", "3+ алтаря разбито."), ("🧚 Крылья", "Первые крылья получены."), ("🍏 500 HP", "Найдены фрукты жизни.")]},
    "endgame": {"name": "🌙 Финал", "items": [("🛸 Полет", "Бесконечный полет."), ("🔫 Башни", "Лунные оружия."), ("🏆 Сет", "Эндгейм броня.")]}
}

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ И СТАРТ
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
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет! Я твой гид. Выбери нужный раздел ниже:"
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, None, state)

# ==========================================
# 👥 РАЗДЕЛ NPC И КАЛЬКУЛЯТОР СЧАСТЬЯ
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Калькулятор счастья", callback_data="n_calc_start"))
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **Раздел NPC**\n\nЗдесь можно изучить жителей или рассчитать их счастье.", reply_markup=builder.as_markup(), parse_mode="Markdown")

# Логика Калькулятора (Шаги)
@dp.callback_query(F.data == "n_calc_start")
async def n_calc_step1(callback: types.CallbackQuery, state: FSMContext):
    biomes = ["Лес", "Снега", "Пустыня", "Джунгли", "Океан", "Освящение", "Пещеры", "Грибной"]
    builder = InlineKeyboardBuilder()
    for b in biomes: builder.add(types.InlineKeyboardButton(text=b, callback_data=f"nc_b:{b}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("🏙 **Шаг 1: Выберите биом:**", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(NPCCalc.choose_biome)

@dp.callback_query(F.data.startswith("nc_b:"))
async def n_calc_step2(callback: types.CallbackQuery, state: FSMContext):
    biome = callback.data.split(":")[1]
    await state.update_data(biome=biome)
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n1:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text(f"🏙 **Биом: {biome}**\n👤 **Шаг 2: Выберите 1-го NPC:**", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(NPCCalc.choose_npc1)

@dp.callback_query(F.data.startswith("nc_n1:"))
async def n_calc_step3(callback: types.CallbackQuery, state: FSMContext):
    npc1 = callback.data.split(":")[1]
    await state.update_data(npc1=npc1)
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❌ Один (без соседа)", callback_data="nc_n2:None"))
    for n in npcs:
        if n['name'] != npc1: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"nc_n2:{n['name']}"))
    builder.adjust(2)
    await callback.message.edit_text(f"👤 **Первый: {npc1}**\n👥 **Шаг 3: Выберите соседа:**", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(NPCCalc.choose_npc2)

@dp.callback_query(F.data.startswith("nc_n2:"))
async def n_calc_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    npc2_name = callback.data.split(":")[1]
    if npc2_name == "None": npc2_name = None
    biome, npc1_name = data['biome'], data['npc1']
    
    res1, f1 = calculate_happiness(npc1_name, npc2_name, biome)
    text = f"📊 **Результат расселения ({biome}):**\n\n👤 **{npc1_name}:**\n└ Цены: `{int(res1*100)}%`\n└ {', '.join(f1) if f1 else 'Нейтрально'}\n"
    
    if npc2_name:
        res2, f2 = calculate_happiness(npc2_name, npc1_name, biome)
        text += f"\n👤 **{npc2_name}:**\n└ Цены: `{int(res2*100)}%`\n└ {', '.join(f2) if f2 else 'Нейтрально'}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Заново", callback_data="n_calc_start"),
                types.InlineKeyboardButton(text="🏠 К NPC", callback_data="m_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs').get('npcs', [])
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Выберите жителя для инфо:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = (f"👤 **{npc['name']}**\n━━━━━━━━━━━━━━\n📥 **Приход:** {npc.get('arrival', 'Стандарт')}\n"
           f"📍 **Биом:** {npc['biome']}\n🎁 **Бонус:** {npc.get('bonus', 'Нет')}\n\n"
           f"❤️ **Любит:** {npc['loves']}\n😊 **Нравится:** {npc['likes']}")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "n_tips")
async def npc_tips(callback: types.CallbackQuery):
    text = "🏡 **Советы:**\n1. Пилоны продаются при счастье < 90%.\n2. Не селите больше 3-х человек в одном месте.\n3. Счастье Медсестры и Гоблина — самое важное для экономии."
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 👾 РАЗДЕЛ БОССОВ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите этап:**", reply_markup=builder.as_markup())

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
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{st}:{k}"),
                types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"),
                types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    txt = get_data('bosses')[st][k].get(fld, "Нет данных.")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text(f"📝 **Инфо:**\n\n{txt}", reply_markup=builder.as_markup(), parse_mode="Markdown")

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
    for i, itm in enumerate(items): builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("🎒 **Топ предметы:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    item = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {item['name']}\n{item['craft']}", show_alert=True)

# ==========================================
# 🧪 АЛХИМИЯ, ЧЕК-ЛИСТЫ И ПРОЧЕЕ
# ==========================================
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"),
                types.InlineKeyboardButton(text="📜 Рецепты", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимия**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    ings = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for i in ings: builder.add(types.InlineKeyboardButton(text=i, callback_data=f"ing:{i}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Сварить!", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 **Выбери 2 ингредиента:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ing(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing)
        await state.update_data(mix=mix)
        await callback.answer(f"Добавлено: {ing}")
    else: await callback.answer("Нельзя добавить!")

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2: return await callback.answer("Нужно 2 ингредиента!")
    res = RECIPES.get(tuple(sorted(mix)), "💥 Бесполезная жижа...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Еще раз", callback_data="alc_craft")).row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🧪 **Результат:**\n\n{res}", reply_markup=builder.as_markup())
    await state.clear()

# ==========================================
# 🧮 КАЛЬКУЛЯТОРЫ (РЕСУРСЫ)
# ==========================================
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы на Сет", callback_data="calc_armor"))
    builder.row(types.InlineKeyboardButton(text="💰 Скидки Гоблина", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Инженерный отдел**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 **Введите цену перековки (в золоте):**")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        txt = (f"💰 **Цены ({p} золота):**\n\n😐 База: {p}\n😊 Скидка 17%: {round(p*0.83, 2)}\n❤️ Скидка 33%: {round(p*0.67, 2)}")
        await message.answer(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup())
        await state.clear()
    except: await message.answer("Введите число!")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
