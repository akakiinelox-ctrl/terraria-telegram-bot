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
# ИМПОРТИРУЕМ АСИНХРОННЫЙ КЛИЕНТ
from groq import AsyncGroq 

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 599835907

# Инициализация АСИНХРОННОГО клиента
if GROQ_API_KEY:
    client = AsyncGroq(api_key=GROQ_API_KEY)
else:
    logging.error("❌ НЕ НАЙДЕН GROQ_API_KEY! ПРОВЕРЬТЕ НАСТРОЙКИ.")
    client = None

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

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def save_user(user_id, username, source="organic"):
    users = get_data('users')
    user_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in users:
        users[user_id] = {"username": username, "join_date": today, "source": source, "last_active": today}
    else:
        users[user_id]["last_active"] = today
        users[user_id]["username"] = username
    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except: pass

# ==========================================
# 🧠 МОЗГ: СВОБОДНЫЙ ЭКСПЕРТ (AsyncGroq)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: Нет API ключа Groq.")
        return

    # ИНСТРУКЦИЯ ДЛЯ БОТА
    system_prompt = (
        "Ты — Гид из игры Terraria. Ты — эксперт, знающий всё о версии 1.4.4. "
        "Твоя цель: помогать игрокам с крафтами, боссами и тактиками."
        "\n\nПРАВИЛА:"
        "\n1. Будь полезным и точным. Не выдумывай предметы."
        "\n2. Используй Markdown (жирный текст, списки)."
        "\n3. Если спрашивают про порядок боссов, дай четкий список."
        "\n4. Если спрашивают крафт, укажи ингредиенты и рабочее место."
        "\n5. Общайся дружелюбно, используй эмодзи (🌲, 🗡️, 💀)."
    )

    try:
        # Асинхронный вызов (важно для Telegram бота)
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            # Используем модель Llama 3 (она очень быстрая и умная)
            model="llama-3.3-70b-versatile", 
            temperature=0.5, 
        )
        
        response = chat_completion.choices[0].message.content
        
        # Кнопки под ответом
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🤔 Спросить что-то ещё", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="Markdown")
        
    except Exception as e:
        # Выводим ошибку в консоль, чтобы ты мог её увидеть в Railway Logs
        print(f"🔴 ОШИБКА AI: {e}") 
        await message_to_edit.edit_text(f"🤯 **Гид:** Ошибка связи с космосом...\nКод ошибки: `{e}`", parse_mode="Markdown")

# --- ОБРАБОТЧИКИ ЧАТА ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer(
        "👋 **Я слушаю, Террариец!**\n\n"
        "Спрашивай о чём угодно:\n"
        "▫️ _Как скрафтить Зенит?_\n"
        "▫️ _Броня на мага перед Плантерой?_\n"
        "▫️ _Кто идет после Пчелы?_"
    )
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def chat_process(message: types.Message, state: FSMContext):
    user_query = message.text
    # Анимация "печатает..."
    sent_msg = await message.answer("🤔 *Гид листает справочник...*")
    # Отправляем запрос ИИ
    await ask_guide_ai(sent_msg, user_query)
    await state.clear()

# ==========================================
# ДАННЫЕ (РЕЦЕПТЫ, ЧЕК-ЛИСТЫ И Т.Д.)
# ==========================================
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крита)",
}

CHECKLIST_DATA = {
    "start": {"name": "🌱 Старт", "items": [("🏠 Дом", "Построй дом"), ("❤️ ХП", "Собери сердца")]},
    "pre_hm": {"name": "🌋 Пре-Хардмод", "items": [("⚔️ Грань Ночи", "Скрафти меч"), ("🌋 Ад", "Сделай мост")]},
}

# ==========================================
# ОБРАБОТЧИКИ КНОПОК
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Задать вопрос Гиду", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"))
    builder.row(types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"),
                types.InlineKeyboardButton(text="🎲 Скучно", callback_data="m_random"))
    
    await message.answer("🛠 **Terraria Tactical Assistant**\nЯ знаю всё об этом мире. Выбери раздел или просто спроси меня!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state=state)

# --- БОССЫ ---
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 До-ХМ", callback_data="b_l:pre_hm"),
                                          types.InlineKeyboardButton(text="🔴 ХМ", callback_data="b_l:hm"))
    builder.add(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Боссы:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses').get(st, {})
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
                types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_info_field(callback: types.CallbackQuery):
    _, st, k, f = callback.data.split(":")
    data = get_data('bosses')[st][k]
    if f == "arena" and "arena_img" in data:
        await callback.message.answer_photo(data["arena_img"], caption=data.get(f, "."), reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data=f"b_s:{st}:{k}")).as_markup())
    else:
        await callback.message.edit_text(data.get(f, "Нет данных"), reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data=f"b_s:{st}:{k}")).as_markup())

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    for c in ["warrior", "ranger", "mage", "summoner"]: builder.row(types.InlineKeyboardButton(text=c, callback_data=f"b_gc:{st}:{k}:{c}"))
    builder.row(types.InlineKeyboardButton(text="⬅️", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("Класс:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_items(callback: types.CallbackQuery):
    _, st, k, c = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][c]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items): builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"alert:{item['craft'][:20]}"))
    builder.row(types.InlineKeyboardButton(text="⬅️", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("Предметы:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("alert:"))
async def show_alert(callback: types.CallbackQuery):
    await callback.answer(callback.data.split(":")[1], show_alert=True)

# --- АЛХИМИЯ ---
@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"),
                types.InlineKeyboardButton(text="📜 Рецепты", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимия**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def alc_craft(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients); await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    for i in ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза"]: builder.add(types.InlineKeyboardButton(text=i, callback_data=f"ing:{i}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Варить", callback_data="alc_mix"))
    await callback.message.edit_text("Выбери 2 ингредиента:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ing(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    d = await state.get_data(); mix = d.get('mix', [])
    if len(mix) < 2 and ing not in mix: mix.append(ing); await state.update_data(mix=mix); await callback.answer(f"+ {ing}")
    else: await callback.answer("Хватит!")

@dp.callback_query(F.data == "alc_mix")
async def alc_mix(callback: types.CallbackQuery, state: FSMContext):
    d = await state.get_data(); mix = d.get('mix', [])
    if len(mix) < 2: await callback.answer("Нужно 2!", show_alert=True); return
    res = RECIPES.get(tuple(sorted(mix)), "Жижа...")
    await callback.message.edit_text(f"Результат: {res}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠", callback_data="to_main")).as_markup())

@dp.callback_query(F.data == "alc_book")
async def alc_book(callback: types.CallbackQuery):
    data = get_data('alchemy').get('sets', {})
    builder = InlineKeyboardBuilder()
    for k, v in data.items(): builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"alcs:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️", callback_data="m_alchemy"))
    await callback.message.edit_text("Рецепты:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("alcs:"))
async def alc_set(callback: types.CallbackQuery):
    k = callback.data.split(":")[1]
    s = get_data('alchemy')['sets'][k]
    t = f"**{s['name']}**\n" + "\n".join([f"🔹 {p['name']}: {p['effect']}" for p in s['potions']])
    await callback.message.edit_text(t, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="alc_book")).as_markup())

# --- КАЛЬКУЛЯТОРЫ ---
@dp.callback_query(F.data == "m_calc")
async def calc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⛏️ Слитки", callback_data="calc_ores"),
                types.InlineKeyboardButton(text="💰 Гоблин", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 Калькуляторы", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ores")
async def calc_ore_sel(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for n, r in {"Медь (3:1)": 3, "Золото (4:1)": 4, "Адамантит (5:1)": 5}.items():
        builder.row(types.InlineKeyboardButton(text=n, callback_data=f"ores:{r}"))
    await callback.message.edit_text("Металл:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ores:"))
async def calc_ore_inp(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(r=callback.data.split(":")[1])
    await state.set_state(CalcState.wait_ore_count)
    await callback.message.answer("Сколько слитков?")

@dp.message(CalcState.wait_ore_count)
async def calc_ore_res(message: types.Message, state: FSMContext):
    try:
        t = int(message.text) * int((await state.get_data())['r'])
        await message.answer(f"Надо руды: {t}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠", callback_data="to_main")).as_markup())
        await state.clear()
    except: await message.answer("Число!")

@dp.callback_query(F.data == "calc_goblin")
async def calc_gob_inp(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.wait_goblin_price)
    await callback.message.answer("Цена (золото):")

@dp.message(CalcState.wait_goblin_price)
async def calc_gob_res(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        await message.answer(f"Скидка: {round(p*0.83, 2)}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠", callback_data="to_main")).as_markup())
        await state.clear()
    except: await message.answer("Число!")

# --- ЗАГЛУШКА ДЛЯ ОСТАЛЬНЫХ КНОПОК ---
@dp.callback_query(F.data.in_({"m_npcs", "m_events", "m_fishing", "m_classes", "m_checklist", "m_random"}))
async def placeholder(callback: types.CallbackQuery):
    await callback.answer("Этот раздел есть в базе! Попробуй спросить Гида словами :)", show_alert=True)

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
