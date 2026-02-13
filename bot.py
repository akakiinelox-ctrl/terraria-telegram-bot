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
from groq import Groq  # Не забудь добавить groq в requirements.txt

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Ключ должен быть в переменных Railway
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
        users[user_id] = {"username": username, "join_date": today, "source": source, "last_active": today, "activity_count": 1}
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
# 🧠 ЛОГИКА ИИ-ГИДА С ПОВЫШЕННОЙ ТОЧНОСТЬЮ
# ==========================================

async def call_groq_guide(message_to_edit: types.Message, query: str, detail_level: str):
    try:
        # Промт с упором на точность Terraria Wiki
        system_instruction = (
            "Ты — Гид из Terraria. Твои знания строго ограничены официальной Terraria Wiki (версия 1.4.4.9+). "
            "Ты должен отвечать максимально точно. Если тебя спрашивают про крафт (например, Зенит), "
            "ты обязан перечислить ВСЕ необходимые компоненты и рабочее место. "
            "Если предмет требует сложной цепочки крафта, распиши её по шагам. "
            "Обращайся к игроку 'Террариец', будь мудрым и дружелюбным. Используй Markdown и эмодзи."
        )
        
        if detail_level == "high":
            system_instruction += " Сейчас дай самый глубокий ответ: укажи шансы дропа, лучшие модификаторы и тактики использования."

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5, # Снижаем температуру для большей точности фактов
        )
        
        response = chat_completion.choices[0].message.content
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📜 Расскажи подробнее", callback_data="guide_more"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        await message_to_edit.edit_text(response, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        await message_to_edit.edit_text("🛰️ **Гид:** Мои мысли спутались... Попробуй спросить ещё раз.")

@dp.callback_query(F.data == "m_search")
async def chat_with_guide_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    await callback.message.answer("👋 **Гид:** Привет, Путник! Я изучил все фолианты этого мира. О чём ты хочешь узнать?")
    await callback.answer()

@dp.message(SearchState.wait_item_name)
async def guide_answer(message: types.Message, state: FSMContext):
    user_query = message.text
    await state.update_data(last_query=user_query)
    sent_msg = await message.answer("🤔 *Гид открывает энциклопедию...*")
    await call_groq_guide(sent_msg, user_query, detail_level="normal")

@dp.callback_query(F.data == "guide_more")
async def guide_more_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_query = data.get("last_query")
    if not last_query:
        await callback.answer("О чём мы говорили?", show_alert=True)
        return
    await callback.answer("Ищу дополнительные детали...")
    await call_groq_guide(callback.message, f"Дай максимально точную и подробную информацию по Wiki для: {last_query}", detail_level="high")

# ==========================================
# 🛡️ АДМИН-ПАНЕЛЬ
# ==========================================
@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 
    users = get_data('users')
    total, active_today, today_str = len(users), 0, datetime.now().strftime("%Y-%m-%d")
    for u in users.values():
        if u.get("last_active") == today_str: active_today += 1
    await message.answer(f"📊 **Всего:** {total}\n🔥 **Сегодня:** {active_today}", parse_mode="Markdown")

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if state: await state.clear()
    ref_source = command.args if command and command.args else "organic"
    save_user(message.from_user.id, message.from_user.username, ref_source)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 Чат с Гидом (Wiki AI)", callback_data="m_search"))
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я помогу тебе. Выбери раздел:"
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback.message, state=state)

# ==========================================
# 📋 ОСТАЛЬНЫЕ РАЗДЕЛЫ (СОХРАНЕНЫ БЕЗ ИЗМЕНЕНИЙ)
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
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    cat, comp = data.get('current_cat'), data.get('completed', [])
    if idx in comp: comp.remove(idx)
    else: comp.append(idx); await callback.answer(f"💡 {CHECKLIST_DATA[cat]['items'][idx][1]}", show_alert=True)
    await state.update_data(completed=comp); await show_checklist(callback.message, cat, comp)

@dp.callback_query(F.data == "chk_res")
async def checklist_result(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat, count = data.get('current_cat'), len(data.get('completed', []))
    total = len(CHECKLIST_DATA[cat]['items'])
    res = f"⚔️ Результат: {count}/{total}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_alchemy")
async def alchemy_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить", callback_data="alc_craft"),
                types.InlineKeyboardButton(text="📜 Рецепты", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("✨ **Алхимия**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "alc_craft")
async def start_crafting(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients); await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    ings = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for i in ings: builder.add(types.InlineKeyboardButton(text=i, callback_data=f"ing:{i}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Варить!", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 Выбери 2 ингредиента:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ing:"))
async def add_ingredient(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing); await state.update_data(mix=mix); await callback.answer(f"+ {ing}")
    await callback.answer()

@dp.callback_query(F.data == "alc_mix")
async def final_mix(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data(); mix = data.get('mix', [])
    if len(mix) < 2: await callback.answer("Нужно 2 предмета!", show_alert=True); return
    res = RECIPES.get(tuple(sorted(mix)), "💥 Жижа...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🧪 Результат: {res}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    ch = [{"title": "🏹 Лучник", "rules": "Только луки", "quest": "Убей Скелетрона"}]
    res = random.choice(ch)
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text(f"🎲 {res['title']}\n{res['quest']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🟢 До-ХМ", callback_data="b_l:pre_hm"),
                                          types.InlineKeyboardButton(text="🔴 ХМ", callback_data="b_l:hm"))
    builder.add(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 Боссы:", reply_markup=builder.as_markup())

# ... (Остальные функции bosses_list, npc_main и т.д. вставляются аналогично без изменений)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
