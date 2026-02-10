import os
import json
import logging
import asyncio
import random  # Добавили модуль для рандома
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
# Вставь свой токен сюда или используй переменную окружения
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЗАГРУЗКА ДАННЫХ ---
def load_json(filename):
    """Универсальная функция загрузки JSON"""
    try:
        file_path = f'data/{filename}'
        if not os.path.exists(file_path):
            logging.error(f"Файл {file_path} не найден!")
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка чтения {filename}: {e}")
        return {}

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="main_bosses"))
    builder.row(types.InlineKeyboardButton(text="👥 NPC и Счастье", callback_data="main_npcs"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы и Билды", callback_data="main_classes"))
    
    await message.answer(
        "👋 **Terraria Helper 2.0**\nЯ знаю всё о крафте, тактиках и билдах.\nВыбери раздел:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    await cmd_start(callback.message)

# ==========================================
# 🛡️ ЛОГИКА КЛАССОВ (ПОДРОБНАЯ + РАНДОМАЙЗЕР)
# ==========================================

# 1. Выбор класса
@dp.callback_query(F.data == "main_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = load_json('classes.json')
    builder = InlineKeyboardBuilder()
    
    # Кнопки классов из JSON
    for key, val in data.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"cls_start:{key}"))
    
    # --- НОВАЯ КНОПКА ДЛЯ СКУЧАЮЩИХ ---
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно (Челлендж)", callback_data="class_random"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ В меню", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Выбери класс:**\nКем ты хочешь играть? Или испытай удачу.", reply_markup=builder.as_markup())

# --- РАНДОМАЙЗЕР ЧЕЛЛЕНДЖЕЙ ---
@dp.callback_query(F.data == "class_random")
async def random_challenge_handler(callback: types.CallbackQuery):
    challenges = [
        "🏹 **Стрелок-Робингуд:** Только луки. Никакого огнестрела и ракетниц!",
        "⚔️ **Истинный Рыцарь:** Только мечи (True Melee). Йо-йо, бумеранги и снаряды мечей запрещены.",
        "🎣 **Рыбак-Воин:** Можно использовать оружие и броню, полученные ТОЛЬКО из рыбалки (Рыба-меч, Акула-пила, Ревершарк).",
        "💣 **Подрывник:** Убивай боссов только взрывчаткой (бомбы, динамит, гранаты).",
        "🧙 **Гарри Поттер:** Только магические жезлы. Книги и магические пушки запрещены.",
        "⛏️ **Шахтер:** Убивай врагов только инструментами (Кирки, Буры, Топоры).",
        "🌵 **Друид:** Используй только снаряжение, связанное с растениями (Кактус, Трава, Листомет, Споры).",
        "🤠 **Ковбой:** Только револьверы и дробовики. Никаких лазеров и автоматического оружия.",
        "👺 **Предатель:** Используй оружие, выпадающее только с мобов того же биома, где ты находишься."
    ]
    
    chal = random.choice(challenges)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎲 Еще раз", callback_data="class_random"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К классам", callback_data="main_classes"))
    
    await callback.message.edit_text(f"🎲 **Твой челлендж на прохождение:**\n\n{chal}", reply_markup=builder.as_markup(), parse_mode="Markdown")

# 2. Выбор этапа игры (Детальный гайд)
@dp.callback_query(F.data.startswith("cls_start:"))
async def class_stage_select(callback: types.CallbackQuery):
    class_id = callback.data.split(":")[1]
    data = load_json('classes.json')
    cls_name = data[class_id]['name']
    
    builder = InlineKeyboardBuilder()
    # Этапы (ключи должны совпадать с JSON)
    stages = {
        "start": "🟢 Старт",
        "pre_hm": "🟡 До Хардмода",
        "hm_start": "🔴 Ранний ХМ",
        "endgame": "🟣 Финал"
    }
    
    for key, name in stages.items():
        builder.add(types.InlineKeyboardButton(text=name, callback_data=f"cls_stage:{class_id}:{key}"))
    builder.adjust(2) 
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Другой класс", callback_data="main_classes"))
    
    await callback.message.edit_text(f"👤 **Класс: {cls_name}**\nВыберите этап игры:", reply_markup=builder.as_markup())

# 3. Меню категорий
@dp.callback_query(F.data.startswith("cls_stage:"))
async def class_category_select(callback: types.CallbackQuery):
    _, class_id, stage_id = callback.data.split(":")
    data = load_json('classes.json')
    stage_info = data[class_id]['stages'][stage_id]
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cls_cat:{class_id}:{stage_id}:armor"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cls_cat:{class_id}:{stage_id}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cls_cat:{class_id}:{stage_id}:accessories"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cls_start:{class_id}"))
    
    await callback.message.edit_text(
        f"📅 **Этап: {stage_info['title']}**\nЧто будем собирать?", 
        reply_markup=builder.as_markup()
    )

# 4. Список предметов
@dp.callback_query(F.data.startswith("cls_cat:"))
async def class_items_list(callback: types.CallbackQuery):
    _, class_id, stage_id, category = callback.data.split(":")
    data = load_json('classes.json')
    items = data[class_id]['stages'][stage_id][category]
    
    builder = InlineKeyboardBuilder()
    for index, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(
            text=item['name'], 
            callback_data=f"cls_item:{class_id}:{stage_id}:{category}:{index}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cls_stage:{class_id}:{stage_id}"))
    
    cat_names = {"armor": "Броня", "weapons": "Оружие", "accessories": "Аксессуары"}
    await callback.message.edit_text(
        f"🎒 **Список: {cat_names.get(category, category)}**\nНажми на предмет, чтобы узнать детали.",
        reply_markup=builder.as_markup()
    )

# 5. Инфо о предмете
@dp.callback_query(F.data.startswith("cls_item:"))
async def class_item_info(callback: types.CallbackQuery):
    _, class_id, stage_id, category, index = callback.data.split(":")
    data = load_json('classes.json')
    item = data[class_id]['stages'][stage_id][category][int(index)]
    
    await callback.answer(
        f"ℹ️ {item['name']}\n\n📝 Где взять:\n{item['info']}",
        show_alert=True
    )

# ==========================================
# 👾 ЛОГИКА БОССОВ
# ==========================================

@dp.callback_query(F.data == "main_bosses")
async def bosses_main_select(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list:hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 Выбери этап игры:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("list:"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = load_json('bosses.json')
    builder = InlineKeyboardBuilder()
    for key, boss in data[stage].items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_bosses"))
    await callback.message.edit_text("👹 Выбери босса:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select:"))
async def boss_main_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    data = load_json('bosses.json')
    boss = data[stage][key]
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экип", callback_data=f"gear_menu:{stage}:{key}"))
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info:{stage}:{key}:tactics"),
        types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"info:{stage}:{key}:arena")
    )
    builder.row(types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info:{stage}:{key}:drops"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list:{stage}"))
    
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("info:"))
async def boss_info_field(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    data = load_json('bosses.json')
    text = data[stage][key].get(field, "Нет информации")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text(f"📝 **Информация:**\n\n{text}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("gear_menu:"))
async def gear_classes_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    classes = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for k, v in classes.items():
        builder.row(types.InlineKeyboardButton(text=v, callback_data=f"class_gear:{stage}:{key}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text("🛡️ Для какого класса показать снаряжение?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("class_gear:"))
async def show_boss_gear_items(callback: types.CallbackQuery):
    _, stage, key, class_id = callback.data.split(":")
    data = load_json('bosses.json')
    items = data[stage][key]['classes'][class_id]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"bg_item:{stage}:{key}:{class_id}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"gear_menu:{stage}:{key}"))
    await callback.message.edit_text(f"🎒 **Рекомендации:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("bg_item:"))
async def boss_gear_craft(callback: types.CallbackQuery):
    _, stage, key, class_id, index = callback.data.split(":")
    data = load_json('bosses.json')
    item = data[stage][key]['classes'][class_id][int(index)]
    await callback.answer(f"🛠 {item['name']}:\n{item['craft']}", show_alert=True)

# ==========================================
# 👥 ЛОГИКА NPC
# ==========================================

@dp.callback_query(F.data == "main_npcs")
async def npc_main_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список NPC", callback_data="npc_list"))
    builder.row(types.InlineKeyboardButton(text="📊 Таблица цен", callback_data="npc_prices"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы", callback_data="npc_tips"))
    builder.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_prices")
async def npc_prices_table(callback: types.CallbackQuery):
    text = "📊 **Таблица Счастья:**\n\n❤️ Восторг (75% цены, Пилон)\n😊 Доволен (88% цены, Пилон)\n😐 Норма (100%)\n☹️ Грусть (112%)\n😡 Ярость (150%)"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_tips")
async def npc_tips_show(callback: types.CallbackQuery):
    text = "🏡 **Связки:**\n\n🔫 Пустыня: Оружейник + Медсестра\n🛠️ Снега: Механик + Гоблин\n🍄 Грибы: Трюфель + Гид"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_list")
async def show_npc_names(callback: types.CallbackQuery):
    data = load_json('npcs.json')
    builder = InlineKeyboardBuilder()
    for npc in data.get('npcs', []):
        builder.add(types.InlineKeyboardButton(text=npc['name'], callback_data=f"npc_info:{npc['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text("👤 Выбери жителя:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("npc_info:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    data = load_json('npcs.json')
    npc = next((n for n in data['npcs'] if n['name'] == name), None)
    text = f"👤 **{npc['name']}**\n📍 Биом: {npc.get('biome', '?')}\n❤️ Любит: {npc.get('loves', '-')}\n😊 Нравится: {npc.get('likes', '-')}"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="npc_list"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# --- ЗАПУСК ---
async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
