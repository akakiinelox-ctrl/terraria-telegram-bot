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
import google.generativeai as genai  # Новая библиотека для поиска

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ОТ_БОТФАЗЕРА"
ADMIN_ID = 599835907  

# ВСТАВЬ СВОЙ КЛЮЧ GEMINI НИЖЕ:
GEMINI_KEY = "AIzaSyDC5DhxG5FBr1WSmVnUJT59BEHtUYE3LLQ" 

# Настройка нейросети
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class CalcState(StatesGroup):
    wait_goblin_price = State()
    wait_ore_count = State()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

# НОВОЕ СОСТОЯНИЕ ДЛЯ ПОИСКА
class SearchState(StatesGroup):
    wait_item_name = State()

# --- ДАННЫЕ ДЛЯ АЛХИМИИ (Твои рецепты) ---
RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье регенерации маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости (+10% крит)",
}

# --- ФУНКЦИИ РАБОТЫ С ДАННЫМИ ---
def load_data(file_name):
    try:
        with open(f"data/{file_name}", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {file_name}: {e}")
        return {}

def log_user(user_id, username):
    try:
        if not os.path.exists("data"): os.makedirs("data")
        file_path = "data/users.json"
        if not os.path.exists(file_path):
            users = {}
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                users = json.load(f)
        
        user_id_str = str(user_id)
        if user_id_str not in users:
            users[user_id_str] = {
                "username": username,
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Log error: {e}")

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    log_user(message.from_user.id, message.from_user.username)
    
    builder = InlineKeyboardBuilder()
    # Новая кнопка поиска в самом верху
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск предмета (AI)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Классы", callback_data="m_classes"))
    builder.row(types.InlineKeyboardButton(text="👹 Боссы", callback_data="m_bosses"))
    builder.row(types.InlineKeyboardButton(text="👨‍🌾 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_bored"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"))
    builder.row(types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="📅 События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькуляторы", callback_data="m_calc"))

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\nЯ твой тактический помощник по Terraria.\nЧто хочешь узнать?",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message)
    await callback.answer()

# --- ЛОГИКА AI ПОИСКА ---
@dp.callback_query(F.data == "m_search")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer("🔍 **Введите название предмета или вопрос:**\n(Например: _Как скрафтить Зенит?_ или _Где найти щит Анх?_)", parse_mode="Markdown")
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def search_item_ai(message: types.Message, state: FSMContext):
    user_query = message.text
    sent_message = await message.answer("⏳ *Ищу в архивах Террарии...*", parse_mode="Markdown")
    
    try:
        prompt = (
            f"Ты эксперт по игре Terraria. Пользователь спрашивает: '{user_query}'. "
            "Дай точный ответ на русском языке. Если это крафт — распиши ингредиенты. "
            "Если предмет из модов (Calamity и т.д.), уточни это. Используй эмодзи."
        )
        
        response = ai_model.generate_content(prompt)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await sent_message.edit_text(response.text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await sent_message.edit_text("❌ Ошибка поиска. Проверьте ключ API.")
    
    await state.clear()

# --- КЛАССЫ ---
@dp.callback_query(F.data == "m_classes")
async def show_classes(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    classes = load_data("classes.json")
    for key, val in classes.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"cls_{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("Выбери свой путь:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cls_"))
async def show_class_stages(callback: types.CallbackQuery):
    class_key = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    data = load_data("classes.json")[class_key]
    for stage_key, stage_val in data['stages'].items():
        builder.row(types.InlineKeyboardButton(text=stage_val['title'], callback_data=f"stg_{class_key}_{stage_key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К классам", callback_data="m_classes"))
    await callback.message.edit_text(f"{data['name']}\n{data['desc']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("stg_"))
async def show_stage_info(callback: types.CallbackQuery):
    _, cls_key, stg_key = callback.data.split("_")
    stage = load_data("classes.json")[cls_key]['stages'][stg_key]
    
    text = f"📍 **{stage['title']}**\n\n"
    text += "🛡 **Броня:**\n" + "\n".join([f"• {i['name']}: {i['info']}" for i in stage['armor']]) + "\n\n"
    text += "⚔️ **Оружие:**\n" + "\n".join([f"• {i['name']}: {i['info']}" for i in stage['weapons']]) + "\n\n"
    text += "💍 **Аксессуары:**\n" + "\n".join([f"• {i['name']}: {i['info']}" for i in stage['accessories']])
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cls_{cls_key}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- БОССЫ ---
@dp.callback_query(F.data == "m_bosses")
async def show_boss_tiers(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🌳 До-хардмод", callback_data="bs_pre_hm"))
    builder.row(types.InlineKeyboardButton(text="💀 Хардмод", callback_data="bs_hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("Выберите этап игры:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("bs_"))
async def show_bosses_list(callback: types.CallbackQuery):
    tier = callback.data.replace("bs_", "")
    builder = InlineKeyboardBuilder()
    bosses = load_data("bosses.json").get(tier, {})
    for b_id, b_data in bosses.items():
        builder.row(types.InlineKeyboardButton(text=b_data['name'], callback_data=f"info_{tier}_{b_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("Выбери босса:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("info_"))
async def show_boss_info(callback: types.CallbackQuery):
    _, tier, b_id = callback.data.split("_")
    boss = load_data("bosses.json")[tier][b_id]
    text = f"👾 **{boss['name']}**\n\n📝 {boss['general']}\n\n⚔️ **Тактика:**\n{boss['tactics']}\n\n🏟 **Арена:**\n{boss['arena']}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎁 Дроп и Классы", callback_data=f"drp_{tier}_{b_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"bs_{tier}"))
    
    if "arena_img" in boss and boss["arena_img"]:
        await callback.message.answer_photo(photo=boss["arena_img"], caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("drp_"))
async def show_boss_drops(callback: types.CallbackQuery):
    _, tier, b_id = callback.data.split("_")
    boss = load_data("bosses.json")[tier][b_id]
    text = f"🎁 **Дроп:** {boss['drops']}\n\n"
    for cls, items in boss['classes'].items():
        text += f"**{cls.capitalize()}:** " + ", ".join([f"{i['name']} ({i['craft']})" for i in items]) + "\n"
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ К боссу", callback_data=f"info_{tier}_{b_id}"))
    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- КАЛЬКУЛЯТОРЫ ---
@dp.callback_query(F.data == "m_calc")
async def show_calcs(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Гоблин (перековка)", callback_data="calc_goblin"))
    builder.row(types.InlineKeyboardButton(text="⛏ Руда -> Слитки", callback_data="calc_ore"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("Что считаем?", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "calc_ore")
async def ore_calc_start(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Медь/Олово/Железо (3:1)", callback_data="ore_3"))
    builder.row(types.InlineKeyboardButton(text="Золото/Платина (4:1)", callback_data="ore_4"))
    builder.row(types.InlineKeyboardButton(text="Адамантит/Титан (5:1)", callback_data="ore_5"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("Выбери тип руды:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ore_"))
async def ore_input_step(callback: types.CallbackQuery, state: FSMContext):
    ratio = callback.data.split("_")[1]
    await state.update_data(current_ratio=ratio)
    await state.set_state(CalcState.wait_ore_count)
    await callback.message.answer("⛏ **Введите количество слитков, которое хотите получить:**")

@dp.message(CalcState.wait_ore_count)
async def ore_input_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        total = int(message.text) * int(data['current_ratio'])
        await message.answer(f"⛏ Для **{message.text}** слитков нужно **{total}** руды.", 
                           reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main")).as_markup())
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
        await message.answer(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main")).as_markup())
        await state.clear()
    except: await message.answer("❌ Введите число!")

# --- АЛХИМИЯ ---
@dp.callback_query(F.data == "m_alchemy")
async def show_alchemy(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧪 Варить зелье", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="📦 Готовые наборы", callback_data="alc_sets"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("Алхимический стол готов:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def alc_craft_start(callback: types.CallbackQuery, state: FSMContext):
    ingredients = sorted(list(set([item for sublist in RECIPES.keys() for item in sublist])))
    builder = InlineKeyboardBuilder()
    for ing in ingredients:
        builder.add(types.InlineKeyboardButton(text=ing, callback_data=f"ing_{ing}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="❌ Сброс", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await state.update_data(selected=[])
    await state.set_state(AlchemyStates.choosing_ingredients)
    await callback.message.edit_text("Выбери 2 ингредиента:", reply_markup=builder.as_markup())

@dp.callback_query(AlchemyStates.choosing_ingredients)
async def alc_process(callback: types.CallbackQuery, state: FSMContext):
    if not callback.data.startswith("ing_"): return
    ing = callback.data.replace("ing_", "")
    data = await state.get_data()
    selected = data.get('selected', [])
    
    if ing not in selected:
        selected.append(ing)
        await state.update_data(selected=selected)
    
    if len(selected) == 2:
        res = RECIPES.get(tuple(sorted(selected)), "🌚 Получилась мутная жижа...")
        await callback.message.answer(f"Результат: {res}")
        await state.clear()
    else:
        await callback.answer(f"Добавлено: {ing}. Нужно еще один!")

@dp.callback_query(F.data == "alc_sets")
async def show_alc_sets(callback: types.CallbackQuery):
    data = load_data("alchemy.json")['sets']
    text = "🧪 **Рекомендуемые наборы:**\n\n"
    for s_id, s_val in data.items():
        text += f"**{s_val['name']}**\n"
        text += "\n".join([f"• {p['name']}: {p['effect']}" for p in s_val['potions']]) + "\n\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- ПРОЧЕЕ (NPC, Рыбалка, События) ---
@dp.callback_query(F.data == "m_npcs")
async def show_npcs(callback: types.CallbackQuery):
    data = load_data("npcs.json")['npcs']
    builder = InlineKeyboardBuilder()
    for npc in data:
        builder.add(types.InlineKeyboardButton(text=npc['name'], callback_data=f"npc_{npc['name'][:10]}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("Список жителей:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_fishing")
async def show_fishing(callback: types.CallbackQuery):
    data = load_data("fishing.json")
    text = "🎣 **Рыбалка в Террарии:**\n\n"
    for biome, fish_list in data['quests'].items():
        text += f"📍 {biome}: " + ", ".join([f["name"] for f in fish_list]) + "\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "m_events")
async def show_events(callback: types.CallbackQuery):
    data = load_data("events.json")
    text = "📅 **События:**\n\n"
    all_ev = {**data['pre_hm'], **data.get('hm', {})}
    for e_id, e in all_ev.items():
        text += f"• {e['name']} (Сложность: {e['difficulty']})\n"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_bored")
async def cmd_bored(callback: types.CallbackQuery):
    challenges = [
        "Убей Глаз Ктулху, используя только медный кинжал!",
        "Построй дом в аду для гида.",
        "Собери 1000 единиц земли.",
        "Вылови 5 ящиков в джунглях.",
        "Победи Короля Слизней без брони."
    ]
    await callback.message.answer(f"🎲 Челлендж для тебя:\n\n_{random.choice(challenges)}_", parse_mode="Markdown")
    await callback.answer()

# --- АДМИНКА ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    users = load_data("users.json")
    await message.answer(f"📊 **Статистика бота:**\nВсего пользователей: {len(users)}")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
