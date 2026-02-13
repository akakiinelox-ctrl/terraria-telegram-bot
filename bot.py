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
from groq import Groq

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 599835907

client = Groq(api_key=GROQ_API_KEY)
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
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

# --- СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ---
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
# 🧠 УНИВЕРСАЛЬНЫЙ ЛОГИЧЕСКИЙ ИИ-ГИД
# ==========================================

async def call_groq_guide(message_to_edit: types.Message, query: str, detail_level: str):
    try:
        system_instruction = (
            "Ты — Гид из Terraria. Твоя главная задача — помогать игрокам, даже если их вопросы нечеткие. "
            "ПРАВИЛА: 1. ИНТЕРПРЕТАЦИЯ: Если пользователь пишет неясно, пойми контекст из Terraria. "
            "2. КОНТЕКСТ: Всегда соотноси вопросы с игрой. 3. ТОЧНОСТЬ: Ориентируйся на актуальную версию 1.4.4+. "
            "4. СТИЛЬ: Ты — мудрый наставник. Используй: 'Путник', 'Террариец', 'Слушай мой совет'. "
            "5. ГИБКОСТЬ: Если запрос широкий, дай обзор и предложи уточнить."
        )
        
        if detail_level == "high":
            system_instruction += " СЕЙЧАС ДАЙ МАКСИМАЛЬНО ГЛУБОКИЙ ОТВЕТ с тактиками и механиками."

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
        )
        
        response = chat_completion.choices[0].message.content
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📜 Расскажи подробнее", callback_data="guide_more"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        await message_to_edit.edit_text("🛰️ **Гид:** Кажется, само мироздание мешает мне ответить... Попробуй еще раз!")

@dp.callback_query(F.data == "m_search")
async def chat_with_guide_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer("👋 **Гид:** Приветствую! О чем ты хочешь поговорить? Спрашивай о чем угодно!")
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def guide_answer(message: types.Message, state: FSMContext):
    user_query = message.text
    if user_query.lower() in ["привет", "хай", "ку"]:
        await message.answer("👋 **Гид:** Приветствую тебя, путник! О чем поведать тебе сегодня?")
        return

    await state.update_data(last_query=user_query)
    sent_msg = await message.answer("🤔 *Гид вглядывается в суть твоего вопроса...*")
    await call_groq_guide(sent_msg, user_query, detail_level="normal")

@dp.callback_query(F.data == "guide_more")
async def guide_more_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_query = data.get("last_query")
    if not last_query:
        await callback.answer("Я потерял нить разговора...", show_alert=True)
        return
    await callback.answer("Ищу глубокие знания...")
    await call_groq_guide(callback.message, f"Расскажи намного подробнее про: {last_query}", detail_level="high")

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
        if u.get("last_active") == today_str:
            active_today += 1

    text = f"📊 **Статистика:**\n👥 Всего: **{total}**\n🔥 Сегодня: **{active_today}**"
    await message.answer(text, parse_mode="Markdown")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    
    ref_source = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Чат с Гидом (AI)", callback_data="m_search"))
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
    await cmd_start(callback.message, state=state)

# ==========================================
# 📋 РАЗДЕЛ: МАСШТАБНЫЙ ЧЕК-ЛИСТ
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
    res = f"⚔️ Результат подготовки: {count}/{total}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

# ==========================================
# 🧪 РАЗДЕЛ: АЛХИМИЯ
# ==========================================
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"),
                types.InlineKeyboardButton(text="📜 Книга рецептов", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимия**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    ings = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for ing in ings: builder.add(types.InlineKeyboardButton(text=ing, callback_data=f"ing:{ing}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Начать варку!", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 Выбери 2 ингредиента:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ingredient(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing)
        await state.update_data(mix=mix)
        await callback.answer(f"Добавлено: {ing}")
    await callback.answer()

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2:
        await callback.answer("Нужно 2 ингредиента!", show_alert=True)
        return
    res = RECIPES.get(tuple(sorted(mix)), "💥 Бесполезная жижа...")
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

# ==========================================
# 🎲 РАНДОМАЙЗЕР
# ==========================================
@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    challenges = [
        {"title": "🏹 Путь Робин Гуда", "quest": "🎯 Победить Скелетрона обычными стрелами."},
        {"title": "🧨 Подрывник", "quest": "🎯 Уничтожить Пожирателя Миров гранатами."},
        {"title": "⚔️ Истинный Рыцарь", "quest": "🎯 Убить Короля Слизней вплотную."}
    ]
    res = random.choice(challenges)
    text = f"🎲 **Челлендж: {res['title']}**\n\n{res['quest']}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# ==========================================
# 👾 РАЗДЕЛ: БОССЫ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите категорию:**", reply_markup=builder.as_markup())

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

# ==========================================
# 👥 РАЗДЕЛ: NPC
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список", callback_data="n_list"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs: builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Выберите NPC:**", reply_markup=builder.as_markup())

# ==========================================
# 🧮 РАЗДЕЛ: КАЛЬКУЛЯТОР
# ==========================================
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⛏️ Слитки -> Руда", callback_data="calc_ores"))
    builder.row(types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 **Калькуляторы**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ores_list(callback: types.CallbackQuery):
    ores = {"Медь (3:1)": 3, "Золото (4:1)": 4, "Адамантит (5:1)": 5}
    builder = InlineKeyboardBuilder()
    for name, ratio in ores.items(): 
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"ore_sel:{ratio}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ **Выбери металл:**", reply_markup=builder.as_markup())

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
        await message.answer(f"⛏ Нужно **{total}** руды.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К меню", callback_data="to_main")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "calc_goblin")
async def goblin_calc_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("💰 **Введите цену (в золоте):**")

@dp.message(CalcState.wait_goblin_price)
async def goblin_calc_finish(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        text = f"💰 **Цена:** {p}\n😊 Скидка: {round(p*0.83, 2)}\n❤️ Макс: {round(p*0.67, 2)}"
        await message.answer(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К меню", callback_data="to_main")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
